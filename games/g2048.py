import asyncio
import random
import itertools

import discord

from gamelib import register
from gamelib.utils import BaseBotApp, GameConfigError

from settings import Z

# Game name
GAME_NAME='2048'
# Reaction buttons
CONTROLS = {'⬅️': 'LEFT', '➡️': 'RIGHT', '⬆️': 'UP', '⬇️': 'DOWN', '🔥': 'FILL'}
# "GAME OVER" in emoji blocks
GAME_OVER = '\n:regional_indicator_g: :regional_indicator_a: :regional_indicator_m: :regional_indicator_e: :white_medium_small_square: :regional_indicator_o: :regional_indicator_v: :regional_indicator_e: :regional_indicator_r: '
# Number Tile to emoji / text mapping
EMOJIS = {
       0: f':white_large_square: `{Z} {Z}`',
       2: f':two: `{Z} {Z}`',
       4: f':four: `{Z} {Z}`',
       8: f':eight: `{Z} {Z}`',
      16: f'`16  {Z}`',
      32: f'`32  {Z}`',
      64: f'`64  {Z}`',
     128: f'`128 {Z}`',
     256: f'`256 {Z}`',
     512: f'`512 {Z}`',
    1024: '`1024`',
    2048: '`2048`',
}

class Board:
    def __init__(self):
        self.board = [[0 for x in range(0,4)] for y in range(0,4)]
        self.score = 0

    def on_move(self, move):
        moved  = False
        moved |= self.shift(move)
        moved |= self.merge(move)
        moved |= self.shift(move)

        if moved:
            self.insert_random()

        return moved, self.is_game_over()

    def render_board(self):
        b = f'Score: {self.score}\n\n'
        for i in range(4):
            for j in range(4):
                b += EMOJIS[self.board[i][j]]
                b += ' '
            b += '\n\n'
        return b + f'\n{Z}'

    def is_game_over(self):
        for i in range(4):
            if 0 in self.board[i]:
                return False
        return not any([self.merge(direction, dry_run=True) for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']])

    def merge(self, move, dry_run=False):
        merged = False

        for x in range(4):
            for y in range(4):
                spot = self.board[x][y]

                if spot != 0:
                    if move == 'UP':
                        # for j in reversed(range(x - 1)):
                        for j in reversed(range(x)):
                            this_spot = self.board[j][y]
                            if spot == this_spot:
                                merged = dry_run or self.merge_two((x, y), (j, y))
                                break
                            if spot != 0:
                                break
                    if move == 'DOWN':
                        for j in range(x + 1, 4):
                            this_spot = self.board[j][y]
                            if spot == this_spot:
                                merged = dry_run or self.merge_two((x, y), (j, y))
                                break
                            if spot != 0:
                                break
                    if move == 'LEFT':
                        # for j in reversed(range(y - 1)):
                        for j in reversed(range(y)):
                            this_spot = self.board[x][j]
                            if spot == this_spot:
                                merged = dry_run or self.merge_two((x, y), (x, j))
                                break
                            if spot != 0:
                                break
                    if move == 'RIGHT':
                        for j in range(y + 1, 4):
                            this_spot = self.board[x][j]
                            if spot == this_spot:
                                merged = dry_run or self.merge_two((x, y), (x, j))
                                break
                            if spot != 0:
                                break

        return merged

    def merge_two(self, what, into):
        this_spot = self.board[into[0]][into[1]]

        self.board[what[0]][what[1]] = 0
        self.board[into[0]][into[1]] = this_spot * 2
        self.score += this_spot * 2

        return True

    def shift(self, move):
        moved = False

        if move in ['UP', 'DOWN']:
            for i in range(4):
                col = [row[i] for row in self.board]
                new_col = sorted(col, key=lambda x: (1 if move is 'UP' else -1) if x == 0 else 0)

                for j in range(4):
                    self.board[j][i] = new_col[j]

                if col != new_col:
                    moved = True

        if move in ['LEFT', 'RIGHT']:
            for i in range(4):
                row = self.board[i]
                new_row = sorted(row, key=lambda x: (1 if move is 'LEFT' else -1) if x == 0 else 0)

                self.board[i] = new_row
                if row != new_row:
                    moved = True

        return moved

    def insert_random(self):
        num = random.choice([2, 2, 4])
        choices = []

        for x, y in itertools.product(range(4), range(4)):
            if self.board[x][y] == 0:
                choices.append((x, y))

        if len(choices) == 0:
            return False

        x, y = random.choice(choices)
        self.board[x][y] = num

        return True


@register(name=GAME_NAME)
class Game2048(BaseBotApp):
    board_msg: discord.Message = None

    def __init__(self, players: list):
        if len(players) > 1:
            raise GameConfigError('This game can only be played by yourself!')

        super().__init__(GAME_NAME, players)

        self.player = players[0]
        self.board = Board()
        self.game_over = False

    async def begin(self, bot, message):
        self.board.insert_random()

        self.board_msg = await message.channel.send(**self.render())
        await self.add_controls(self.board_msg)

        self.register_message(self.board_msg)

    async def end(self):
        self.game_over = True

        await self.board_msg.edit(**self.render())
        await self.board_msg.clear_reactions()

        self.unregister_message(self.board_msg)

    async def notify(self, event, **data):
        if event == 'react':
            user = data.get('user')
            reaction = data.get('reaction')

            move = CONTROLS.get(reaction.emoji)
            await reaction.remove(user)

            if move:
                if move == 'FILL':
                    for _ in range(16):
                        self.board.insert_random()
                    await self.board_msg.edit(**self.render())
                    return

                moved, game_over = self.board.on_move(move)

                if moved:
                    await self.board_msg.edit(**self.render())

                    if game_over:
                        self.game_over = True
                        self.end_session()
                        await self.end()

    def render(self):
        board_str = self.board.render_board()

        if self.game_over:
            board_str += GAME_OVER

        embed = discord.Embed(title='Play 2048', description=board_str)

        return {'embed': embed}

    async def add_controls(self, message):
        for c in CONTROLS.keys():
            await message.add_reaction(c)
