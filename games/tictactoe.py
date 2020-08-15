import random
import itertools

import discord

from gamelib import register
from gamelib.utils import BaseBotApp, GameConfigError, TurnMessage

from settings import Z

GAME_NAME = 'tictactoe'
CONTROLS = {'1️⃣':0, '2️⃣':1, '3️⃣':2, '🥇':3, '🥈':4, '🥉':5}
REVERSE_ROW = {0:'1️⃣', 1:'2️⃣', 2: '3️⃣', None:'?'}
REVERSE_COL = {0:'🥇', 1:'🥈', 2: '🥉', None:'?'}
GAME_OVER = '\n:regional_indicator_g: :regional_indicator_a: :regional_indicator_m: :regional_indicator_e: :white_medium_small_square: :regional_indicator_o: :regional_indicator_v: :regional_indicator_e: :regional_indicator_r: '


@register(name=GAME_NAME)
class TicTacToe(BaseBotApp):
    channel: discord.TextChannel = None
    board_msg: discord.Message = None

    def __init__(self, players: list):
        if len(players) < 2:
            raise GameConfigError("You didn't tell me who to play this game with!")

        if len(players) > 2:
            raise GameConfigError("That's too many people! This game can only be played with 2 people.")

        super().__init__(GAME_NAME, players)

        self.board = [[0, 0, 0] for _ in range(3)]
        self.game_over = False
        self.player1 = players[0]
        self.player2 = players[1]
        self.current_player = random.choice(players)

        self.emojis = {
            0: ':white_large_square:',
            self.player1: ':negative_squared_cross_mark:',
            self.player2: ':blue_circle:'
        }
        self.other = {
            self.player1: self.player2,
            self.player2: self.player1
        }
        self.selected_row = None
        self.selected_col = None
        self.status_message = ''
        self.winner = None

    async def begin(self, bot, message: discord.Message):
        self.bot = bot
        self.channel: discord.TextChannel = message.channel
        self.turn_message = TurnMessage(self.channel)

        await self.update_message()
        await self.add_controls()
        await self.update_turn_message()

        if self.current_player.id == self.bot.user.id:
            await self.play_bot_move()

        self.register_message(self.board_msg)

    async def end(self):
        self.game_over = True
        self.status_message = ''

        await self.turn_message.cleanup()
        await self.clear_controls()
        await self.update_message()

        self.unregister_message(self.board_msg)

    async def handle(self, event, **data):
        if event == 'reaction':
            user = data.get('user')
            reaction = data.get('reaction')

            move = CONTROLS.get(reaction.emoji)
            await reaction.remove(user)

            if move != None and (user.id == self.current_player.id):
                if move > 2:
                    self.selected_col = move - 3
                else:
                    self.selected_row = move

                self.status_message = ''

                if self.selected_row != None and self.selected_col != None:
                    await self.play_move()

                await self.update_message()
                await self.update_turn_message()

                if not self.winner and self.current_player.id == self.bot.user.id:
                    await self.play_bot_move()

    async def play_move(self):
        row, col = self.selected_row, self.selected_col

        if self.board[row][col] == 0:
            self.board[row][col] = self.current_player
            self.current_player = self.other[self.current_player]
        else:
            self.status_message = "That's taken, choose another spot!"

        self.selected_row = None
        self.selected_col = None

        winner = self.check_winner()
        if winner:
            self.winner = winner
            await self.end()
            self.end_session()
            return

    async def play_bot_move(self):
        self.bot_move()
        self.current_player = self.other[self.current_player]

        winner = self.check_winner()
        if winner:
            self.winner = winner
            await self.end()
            self.end_session()
            return

        await self.update_message()
        await self.update_turn_message()

    async def update_message(self):
        if self.board_msg:
            await self.board_msg.edit(**self.render())
            return

        self.board_msg = await self.channel.send(**self.render())

    async def update_turn_message(self):
        await self.turn_message.edit('...')
        self.turn_message.delay(f'{self.current_player.mention} it is your turn in Tic-Tac-Toe!')

    def render(self):
        board_str = ''

        if not self.winner:
            board_str = f'Selected: ({REVERSE_ROW[self.selected_row]}, {REVERSE_COL[self.selected_col]})\n\n'

        board_str += f'`{Z}    {Z}` '
        for col in range(3):
            board_str += REVERSE_COL[col] + f' `{Z} {Z}` '
        board_str += '\n\n'

        for row in range(3):
            board_str += REVERSE_ROW[row] + f' `{Z} {Z}` '
            for col in range(3):
                board_str += self.emojis[self.board[row][col]] + f' `{Z} {Z}` '
            board_str += '\n\n'

        if not self.winner:
            board_str += f'{self.current_player.mention} {self.status_message}'
        elif self.winner == 'TIE':
            board_str += f"It's a tie!\n"
        else:
            board_str += f'{self.winner.mention} **has won**!\n'

        if self.game_over:
            board_str += f'\n{GAME_OVER}'

        embed = discord.Embed(
            title=f'Tic Tac Toe: {self.player1.name} and {self.player2.name}',
            description=board_str
        )

        return {'embed': embed}

    async def add_controls(self):
        for c in CONTROLS.keys():
            await self.board_msg.add_reaction(c)

    async def clear_controls(self):
        await self.board_msg.clear_reactions()

    def check_winner(self):
        for row_i in range(3):
            row = self.board[row_i]
            if row[0] == row[1] and row[1] == row[2]:
                if row[0] != 0:
                    return row[0]

        for col_i in range(3):
            if self.board[0][col_i] == self.board[1][col_i] and self.board[1][col_i] == self.board[2][col_i]:
                if self.board[0][col_i] != 0:
                    return self.board[0][col_i]

        if self.board[0][0] == self.board[1][1] and self.board[1][1] == self.board[2][2]:
            if self.board[0][0] != 0:
                return self.board[0][0]

        if self.board[0][2] == self.board[1][1] and self.board[1][1] == self.board[2][0]:
            if self.board[0][2] != 0:
                return self.board[0][0]

        for row_i in range(3):
            if 0 in self.board[row_i]:
                return None

        return 'TIE'

    def bot_move(self):
        choices = []

        for row, col in itertools.product(range(3), range(3)):
            if self.board[row][col] == 0:
                choices.append((row, col))

        row, col = random.choice(choices)

        self.board[row][col] = self.bot.user
