import os

import discord
from discord.ext import commands

from gamelib import registry, sessionManager, preferences
from gamelib.utils import setupLogger

import games

PREFIX = 'g!'
DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY') \
                  or 'NzEzMjYxMzAwNjQxNDMxNjE0.XsdnvA.Pv14UxDnRbKK1pFcEwoDRbM5zBA'

bot = commands.Bot(command_prefix=PREFIX)
logger = setupLogger()


@bot.event
async def on_ready():
    logger.info(f'Logged on as {bot.user.name}')


@bot.command('play', help='Play a game')
async def play(ctx: commands.Context, game_name: str = ''):
    # Game name is not specified
    if not game_name:
        return await ctx.send('Huh? You don\'t want to play any particular game?')

    # Get the opponent
    opponent = ctx.message.mentions and ctx.message.mentions[0]
    if not opponent:
        return await ctx.send(f"You didn't tell me who to play this game with!")

    # Make sure the game exists
    if not registry.get(game_name):
        return await ctx.send(f'I don\'t know what that game is!')

    # Instantiate game
    game = registry.get(game_name)()
    success = sessionManager.add(ctx.message.author, opponent, game)

    # Check if session already existed
    if not success:
        return await ctx.send(f"Session already exists... `{PREFIX}resign` the game first!")

    # Woohoo! let's get started
    await ctx.send(f'Challenging {opponent.mention}...')
    messages = await game.begin(bot, ctx.message, player1=ctx.author, player2=opponent)

    # Register messages for event handling
    for message in messages:
        sessionManager.register_message(message, game)


@bot.command('end', help='End an ongoing game')
async def end(ctx: commands.Context):
    # Get the opponent
    opponent = ctx.message.mentions and ctx.message.mentions[0]
    if not opponent:
        return await ctx.send(f"You didn't tell me which game to end!")

    # Find the session
    game = sessionManager.pop(ctx.author, opponent)
    if not game:
        return await ctx.send(f'No game found between {ctx.message.author.mention} and {opponent.mention}')

    # End this for good
    messages = await game.end()
    await ctx.send(f'Resigned game with {opponent.mention}')

    # Unregister messages for event handling
    for message in messages:
        sessionManager.unregister_message(message, game)


@bot.command('prefs', help='View game settings')
async def prefs(ctx: commands.Context, app: str = None, key: str = None):
    # Find the session
    prefs = preferences.get(ctx.author)

    try:
        # Dump all user settings
        if not app:
            msg = 'Your Preferences:\n'
            for app, settings in prefs.items():
                if app != 'id':
                    msg += f'\n**__{app}__**'
                    for key, value in settings.items():
                        msg += f'\n{key} = {value}'

            return await ctx.send(msg)

        # Make sure the game exists
        if app != 'global' and not registry.get(app):
            return await ctx.send(f'I don\'t know what that app is!')

        # Dump all settings for specified app
        if not key:
            msg = f"Your Preferences for **{app}**:\n"
            for key, value in prefs[app].items():
                msg += f'\n{key} = {value}'
            return await ctx.send(msg)

        msg = f'{key} = {prefs[app][key]}'
        await ctx.send(msg)
    except KeyError:
        await ctx.send('Whoops! It seems that a specified param does not exist in your settings... maybe you haven\'t customized that yet?\n*Or, my code threw a python KeyError for some odd reason...*')


@bot.command('set', help='Customize game settings')
async def prefs(ctx: commands.Context, app: str = None, key: str = None, value: str = None):
    # Check for app, or send usage
    if not app:
        return await ctx.send(f"Usage: `{PREFIX}set APP KEY VALUE` where APP is 'global' or a game name")

    # Validate key and value exist
    if not key or not value:
        return await ctx.send(f'Key and value have to be specified')

    # Make sure the game exists
    if app != 'global' and not registry.get(app):
        return await ctx.send(f'I don\'t know what that app is!')

    # Set the settings
    preferences.set(ctx.author, app, key, value)
    return await ctx.send(f'{key} = {value}')


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user):
    # Skip self-reactions
    if user == bot.user:
        return

    # Notify app about reaction
    app = sessionManager.get_player_session(user)
    # app = sessionManager.get_message_session(reaction.message)
    if app:
        await app.notify('react', reaction=reaction, user=user)


if not DISCORD_API_KEY:
    logger.error("ERROR: Set the env variable 'DISCORD_API_KEY'")
    exit(1)


bot.run(DISCORD_API_KEY)
