import discord
import random

from gamelib import register, preferences
from gamelib.utils import BaseBotApp, TurnMessage, GameConfigError

GAME_NAME = 'connect4'
PREFERENCES = {
    'emoji': 'Game board emoji',
    'color': 'Message embed color'
}

@register(name=GAME_NAME, prefs=PREFERENCES)
class GameConnect4(BaseBotApp):
    BOARD_X = 7
    BOARD_Y = 6
    BUTTONS = {'1️⃣':0,'2️⃣':1,'3️⃣':2,'4️⃣':3,'5️⃣':4,'6️⃣':5,'7️⃣':6}
    WINNER_BUTTONS = {'🎉':0,'🇺':1,'🎊':2,'🇼':3,'🇴':5,'🇳':6,'🍾':7}
    BLANK_TILE = "➕"
    PRIMARY_TILE = "🟠"
    TERTIARY_TILE = "🔵"
    PRIMARY_COLOR = (255,175,44)
    TERTIARY_COLOR = (84,174,239)

    def __init__(self, bot, players: list, channel: discord.TextChannel):
        if len(players) < 2:
            raise GameConfigError("You didn't tell me who to play this game with!")

        if len(players) > 2:
            raise GameConfigError("That's too many people! This game can only be played with 2 people.")

        super().__init__(GAME_NAME, players)

        self.bot = bot
        self.channel = channel
        self.primary = players[0]
        self.tertiary = players[1]

        self.has_buttons = False
        self.winner = None

    async def begin(self):
        self.board = [[None for _ in range(0,7)] for _ in range(0,6)]

        if self.tertiary != self.bot.user:
            self.current_player = random.choice([self.primary, self.tertiary])
        else:
            self.current_player = self.primary

        self.turn_message = TurnMessage(self.channel)
        self.message = await self.channel.send(f'{self.primary.name} started session between {self.primary.name} and {self.tertiary.name}')

        await self.render_message()
        self.register_message(self.message)

    async def end(self):
        await self.turn_message.cleanup()
        await self.message.clear_reactions()
        self.unregister_message(self.message)

    async def handle(self, event, **data):
        if event == 'reaction':
            user = data.get('user')
            reaction = data.get('reaction')

            await reaction.remove(user)

            if self.is_player_current(user):
                col = self.BUTTONS[reaction.emoji]
                await self.play_move(col, user)

            if self.is_completed():
                self.end_session()

    def is_completed(self):
        return True if self.winner else False

    def detect_current_player_win(self):
        for col in range(0, self.BOARD_X-3):
            for row in range(0, self.BOARD_Y):
                if self.board[row][col] == self.board[row][col+1] == self.board[row][col+2] == self.board[row][col+3] == self.current_player.id:
                    return True

        for row in range(0, self.BOARD_Y-3):
            for col in range(0, self.BOARD_X):
                if self.board[row][col] == self.board[row+1][col] == self.board[row+2][col] == self.board[row+3][col] == self.current_player.id:
                    return True

        for row in range(3, self.BOARD_Y):
            for col in range(0, self.BOARD_X-3):
                if self.board[row][col] == self.board[row-1][col+1] == self.board[row-2][col+2] == self.board[row-3][col+3] == self.current_player.id:
                    return True

        for row in range(3, self.BOARD_Y):
            for col in range(3, self.BOARD_X):
                if self.board[row][col] == self.board[row-1][col-1] == self.board[row-2][col-2] == self.board[row-3][col-3] == self.current_player.id:
                    return True

        return False

    async def play_move(self, col, user):
        ret_val = False
        for y in range(5,-1,-1):
            if not self.board[y][col]:
                self.board[y][col] = user.id
                if self.detect_current_player_win():
                    self.winner = self.current_player
                else:
                    self.current_player = self.primary if self.is_player_current(self.tertiary) else self.tertiary
                await self.render_message()
                ret_val = True
                break

        # bot AI code
        if self.tertiary.id == self.bot.user.id and self.is_player_current(self.tertiary):
            cols = list(self.BUTTONS.values())
            random.shuffle(cols)
            escape = False
            for col in cols:
                if escape:
                    break
                for y in range(5,-1,-1):
                    if not self.board[y][col]:
                        self.board[y][col] = self.tertiary.id
                        if self.detect_current_player_win():
                            self.winner = self.current_player
                        else:
                            self.current_player = self.primary if self.is_player_current(self.tertiary) else self.tertiary
                        await self.render_message()
                        escape = True
                        break

        return ret_val
    async def render_message(self):
        if not self.winner:
            header = f"It's your move, {self.current_player.name}"
        else:
            header = f"Congratulations, {self.winner.name}"
        container = discord.Embed(title=header, color=self.get_container_color())
        container.add_field(name=self.render_board(), value="⠀", inline=True)
        await self.message.edit(content=f"{self.primary.mention} ⚔️ {self.tertiary.mention}", embed=container)
        await self.refresh_buttons()

        if not self.winner:
            self.turn_message.delay(f'{self.current_player.mention} It\'s your turn in connect 4!')

    def is_player_current(self, player):
        return self.current_player == player

    def get_container_color(self):
        primary_color = self.preference(self.primary, 'color') or self.PRIMARY_COLOR
        tertiary_color = self.preference(self.tertiary, 'color') or self.TERTIARY_COLOR

        return discord.Color.from_rgb(*primary_color) if \
            self.current_player == self.primary \
            else discord.Color.from_rgb(*tertiary_color)

    def get_player_emojis(self):
        primary_tile = self.preference(self.primary, 'emoji') or self.PRIMARY_TILE
        tertiary_tile = self.preference(self.tertiary, 'emoji') or self.TERTIARY_TILE

        return primary_tile, tertiary_tile

    def render_board(self):
        primary_tile, tertiary_tile = self.get_player_emojis()
        ret = ""
        for y in self.board:
            for tile in y:
                if tile is self.primary.id:
                    ret += f"{primary_tile}\t\t"
                elif tile is self.tertiary.id:
                    ret += f"{tertiary_tile}\t\t"
                else:
                    ret += f"{self.BLANK_TILE}\t\t"
            ret += "\n\n\n"
        if not self.winner:
            ret += '\t\t'.join(self.BUTTONS.keys())
        else:
            ret += '\t\t'.join(self.WINNER_BUTTONS.keys())
        return ret

    async def refresh_buttons(self):
        if not self.winner and not self.has_buttons:
            for emoji in self.BUTTONS.keys():
                await self.message.add_reaction(emoji)
            self.has_buttons = True
        elif self.winner:
            await self.message.clear_reactions()
