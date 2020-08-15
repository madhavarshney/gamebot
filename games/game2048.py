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

    def make_move(self, move):
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
        for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            if self.merge(direction, dry_run=True):
                return False
        return True

    def merge(self, move, dry_run=False):
        merged = False

        if move == 'UP':
            iterator = itertools.product(range(3), range(4))
        if move == 'DOWN':
            iterator = itertools.product(reversed(range(1, 4)), range(4))
        if move == 'LEFT':
            iterator = itertools.product(range(4), range(3))
        if move == 'RIGHT':
            iterator = itertools.product(range(4), reversed(range(1, 4)))

        for row, col in iterator:
            spot = self.board[row][col]

            if spot != 0:
                next_spots = {'UP': row + 1, 'DOWN': row - 1, 'LEFT': col + 1, 'RIGHT': col - 1}
                next_i = next_spots[move]

                if move in ['UP', 'DOWN']:
                    next_spot = self.board[next_i][col]
                    sp = (next_i, col)
                if move in ['LEFT', 'RIGHT']:
                    next_spot = self.board[row][next_i]
                    sp = (row, next_i)

                if next_spot == spot:
                    merged = dry_run or self.merge_two(sp, (row, col))

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
                # Create a new array based on the column
                col = [row[i] for row in self.board]
                # Push all the zeroes to either edges
                new_col = sorted(col, key=lambda x: (1 if move is 'UP' else -1) if x == 0 else 0)

                for j in range(4):
                    self.board[j][i] = new_col[j]

                if col != new_col:
                    moved = True

        if move in ['LEFT', 'RIGHT']:
            for i in range(4):
                row = self.board[i]
                # Push all the zeroes to either ends
                new_row = sorted(row, key=lambda x: (1 if move is 'LEFT' else -1) if x == 0 else 0)

                self.board[i] = new_row
                if row != new_row:
                    moved = True

        return moved

    def insert_random(self):
        num = random.choice([2, 2, 4])
        choices = []

        # Find all empty spaces
        for row, col in itertools.product(range(4), range(4)):
            if self.board[row][col] == 0:
                choices.append((row, col))

        if len(choices) == 0:
            return False

        # Fill in a random empty choice
        row, col = random.choice(choices)
        self.board[row][col] = num

        return True


class SubGame:
    def __init__(self, player, channel):
        self.board = Board()
        self.player = player
        self.channel = channel
        self.board_msg = None
        self.game_over = False

    async def begin(self):
        self.board.insert_random()

        await self.update_message()
        await self.add_controls()

    async def end(self):
        self.game_over = True

        await self.update_message()
        await self.clear_controls()

    async def make_move(self, move):
        if self.game_over:
            return

        if move == 'FILL':
            while True:
                success = self.board.insert_random()
                if not success:
                    break
            await self.update_message()
            return

        moved, game_over = self.board.make_move(move)

        if not moved:
            return

        await self.update_message()

        if game_over:
            await self.end()

    async def update_message(self):
        if not self.board_msg:
            self.board_msg = await self.channel.send(**self.render())
        else:
            await self.board_msg.edit(**self.render())

    def render(self):
        board_str = self.board.render_board()
        board_str += f'{self.player.mention}'

        if self.game_over:
            board_str += f'\n{GAME_OVER}'

        embed = discord.Embed(
            title=f'Play 2048: {self.player.name}',
            description=board_str
        )

        return {'embed': embed}

    async def add_controls(self):
        for c in CONTROLS.keys():
            await self.board_msg.add_reaction(c)

    async def clear_controls(self):
        await self.board_msg.clear_reactions()


@register(name=GAME_NAME)
class Game2048(BaseBotApp):
    def __init__(self, bot, players: list, channel: discord.TextChannel):
        super().__init__(GAME_NAME, players)

        self.channel = channel
        self.games = {}

        for player in players:
            self.games[player.id] = SubGame(player, channel)

    async def begin(self):
        for game in self.games.values():
            await game.begin()
            self.register_message(game.board_msg)

    async def end(self):
        score = 0
        winner = None

        for game in self.games.values():
            # TODO: handle ties
            if game.board.score > score:
                score = game.board.score
                winner = game.player

            await game.end()
            self.unregister_message(game.board_msg)

        if winner and len(self.games.values()) > 1:
            await self.channel.send(f'{winner.mention} has won with a score of {score}!')

        self.end_session()

    async def handle(self, event, **data):
        if event == 'reaction':
            user = data.get('user')
            reaction = data.get('reaction')

            move = CONTROLS.get(reaction.emoji)
            await reaction.remove(user)

            if move and (user.id in self.games):
                game = self.games[user.id]
                await game.make_move(move)

                if game.game_over:
                    # TODO: multiplayer (3+)
                    await self.end()
