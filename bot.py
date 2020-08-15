import asyncio
import signal
import os

import discord
from discord.ext import commands

from gamelib import registry, sessionManager, preferences
from gamelib.utils import setupLogger, GameConfigError

import games
import settings

PREFIX = 'g!'
DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY')


class ModdedBot(commands.Bot):
    async def close(self, *args, **kwargs):
        await sessionManager.killall()
        await super().close(*args, **kwargs)


logger = setupLogger()
bot = ModdedBot(command_prefix=PREFIX)
bot.remove_command('help')


@bot.event
async def on_ready():
    logger.info(f'Logged on as {bot.user.name}')


@bot.command('help')
async def help(ctx: commands.Context):
    embed = (
        discord.Embed(
            title=settings.MAIN_TITLE,
            url=settings.MAIN_URL,
            description=settings.HELP_DESCRIPTION,
            color=discord.Color.from_rgb(8,146,208)
        )
            .set_author(
                name=settings.AUTHOR_NAME,
                icon_url=settings.AUTHOR_ICON,
                url=settings.AUTHOR_LINK
            )
            .set_thumbnail(url=settings.GAME_IMG)
            .set_footer(
                text=settings.FOOTER_TEXT,
                icon_url=settings.BUG_EMOJI
            )
    )
    await ctx.send(embed=embed)


@bot.command('play', help='Play a game')
async def play(ctx: commands.Context, game_name: str = ''):
    # Game name is not specified
    if not game_name:
        return await ctx.send(f"Usage: `g!play GAME [@opponent]`\nAvailable games are {', '.join(registry.all())}")

    # Make sure the game exists
    game_cls = registry.get(game_name)
    if not game_cls:
        return await ctx.send(f'I don\'t know what that game is! Use `g!play` to list available games.')

    # Get the players
    players: list = ctx.message.mentions or []
    if ctx.author not in players:
        players.insert(0, ctx.author)

    # Formatted list of people
    people = ' and '.join(map(lambda p: p.mention, players))

    # Check if session already existed
    if sessionManager.get(players):
        return await ctx.send(f'Game with {people} already exists... `{PREFIX}end` the game first!')

    # Instantiate game
    try:
        game = game_cls(bot, players, ctx.message.channel)
    except GameConfigError as err:
        return await ctx.send(f"Whoops: {err.message}")

    # Woohoo! let's get going
    sessionManager.add(players, game)
    await game.begin()


@bot.command('end', help='End an ongoing game')
async def end(ctx: commands.Context):
    # Get the players
    players: list = ctx.message.mentions or []
    if ctx.author not in players:
        players.insert(0, ctx.author)

    # Formatted list of people
    people = ' and '.join(map(lambda p: p.mention, players))

    # Find the session
    game = sessionManager.pop(players)
    if not game:
        return await ctx.send(f'No game found with {people}')

    # End this for good
    await game.end()
    await ctx.send(f'Ended game with {people}')


@bot.command('prefs', help='View game settings')
async def get_prefs(ctx: commands.Context, app: str = None, key: str = None):
    try:
        # Dump all user settings
        if not app:
            prefs = preferences.get_all(ctx.author)
            msg = 'Your Preferences:\n'
            for app, settings in prefs.items():
                if app != 'id':
                    msg += f'\n**__{app}__**'
                    for key, value in settings.items():
                        msg += f'\n{key} = {value}'

            return await ctx.send(msg)

        # Make sure the game exists
        if app != 'global' and not registry.get(app):
            return await ctx.send(f'I\'m not sure what app or game that is!')

        # Dump all settings for specified app
        if not key:
            prefs = preferences.get_all_for_app(ctx.author, app)
            msg = f"Your Preferences for **{app}**:\n"
            for key, value in prefs.items():
                msg += f'\n{key} = {value}'
            return await ctx.send(msg)

        msg = f'{key} = {preferences.get(ctx.author, app, key)}'
        await ctx.send(msg)

    except KeyError:
        await ctx.send('Whoops! It seems that a specified param does not exist in your settings... maybe you haven\'t customized that yet?\n*Or, my code threw a python KeyError for some odd reason...*')


@bot.command('set', help='Customize game settings')
async def set_prefs(ctx: commands.Context, app: str = None, key: str = None, value: str = None):
    # Check for app, or send usage
    if not app:
        return await ctx.send(f"Usage: `{PREFIX}set APP KEY VALUE` where APP is 'global' or a game name")

    # Make sure the game exists
    if app != 'global' and not registry.get(app):
        return await ctx.send(f'I don\'t know what that app is!')

    # Validate key and value exist
    if not key:
        return await ctx.send(f'Key has to be specified')

    # Verify requested setting exists (can be customized)
    if not preferences.exists(app, key):
        return await ctx.send('That app / key combo cannot be customized! Are you sure that setting exists?')

    # Validate key and value exist
    if not value:
        return await ctx.send(f'Value has to be specified')

    # Set the settings
    preferences.set(ctx.author, app, key, value)
    await ctx.send(f'{key} = {value}')

    # Notify apps
    sessions = sessionManager.get_player_sessions(ctx.author)
    for app in sessions:
        await app.handle('preference_change', user=ctx.author)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user):
    # Skip self-reactions
    if user == bot.user:
        return

    # Find the player's sessions and the message's app
    sessions = sessionManager.get_player_sessions(user)
    app = sessionManager.get_message_session(reaction.message)

    # Notify app about reaction
    if app:
        if sessions and app in sessions:
            await app.handle('reaction', reaction=reaction, user=user)
        else:
            await reaction.remove()


if not DISCORD_API_KEY:
    logger.error("ERROR: Set the env variable 'DISCORD_API_KEY'")
    exit(1)


loop = asyncio.get_event_loop()
raised = False

def raise_only_once(signum, frame):
    global raised

    if not raised:
        raised = True
        raise KeyboardInterrupt

signal.signal(signal.SIGINT, raise_only_once)

try:
    loop.run_until_complete(bot.start(DISCORD_API_KEY))
except KeyboardInterrupt:
    loop.run_until_complete(bot.close())
finally:
    loop.close()
