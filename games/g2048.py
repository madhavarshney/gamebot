import asyncio
import random
import discord

from gamelib import register
from gamelib.utils import BotApp

EMOJIS = {
       0: ':white_large_square: ` `',
       2: ':two: ` `',
       4: ':four: ` `',
       8: ':eight: ` `',
      16: '`16  `',
      32: '`32  `',
      64: '`64  `',
     128: '`128 `',
     256: '`256 `',
     512: '`512 `',
    1024: '`1024`',
    2048: '`2048`',
}


CONTROLS = {'⬅️': 'LEFT', '➡️': 'RIGHT', '⬆️': 'UP', '⬇️': 'DOWN'}

@register(name='2048')
class Game2048(BotApp):
    board = None
    score = 0
    player = None
    board_msg: discord.Message = None

    async def begin(self, bot, message, player1, player2):
        # self.player = message.author
        self.player = player1
        self.board = [[0 for x in range(0,4)] for y in range(0,4)]
        self.score = 0

        self.board_msg = await message.channel.send(self.render_board())
        await self.add_controls(self.board_msg)

        return [self.board_msg]

    async def end(self):
        # "GAME OVER" in emoji blocks
        GAME_OVER = '\n:regional_indicator_g: :regional_indicator_a: :regional_indicator_m: :regional_indicator_e:   :regional_indicator_o: :regional_indicator_v: :regional_indicator_e: :regional_indicator_r: '

        await self.board_msg.edit(content=self.render_board() + GAME_OVER)
        await self.board_msg.clear_reactions()

        return [self.board_msg]

    async def notify(self, event, **data):
        if event == 'react':
            user = data.get('user')
            reaction = data.get('reaction')

            move = CONTROLS.get(reaction.emoji)
            await reaction.remove(self.player)

            if not move:
                return

            game_over = self.on_move(move)
            await self.board_msg.edit(content=self.render_board())

            if game_over:
                super().end_session(self.player, self.player)
                await message.channel.send('Game over!')

    def on_move(self, move):
        self.merge(move)
        self.shift(move)
        return self.insert_random()

    def render_board(self):
        b = f'2048 [Score: {self.score}]\n\n'
        for i in range(4):
            for j in range(4):
                b += EMOJIS[self.board[i][j]]
                b += '    '
            b += '\n\n'
        return b + '\n.'

    async def add_controls(self, message):
        for c in CONTROLS.keys():
            await message.add_reaction(c)

    def merge(self, move):
        for x in range(4):
            for y in range(4):
                spot = self.board[x][y]

                if spot != 0:
                    if move == 'UP':
                        # for j in reversed(range(x - 1)):
                        for j in reversed(range(x)):
                            this_spot = self.board[j][y]
                            if spot == this_spot:
                                self.board[x][y] = 0
                                self.board[j][y] = this_spot * 2
                                self.score += this_spot * 2
                                break
                            if spot != 0:
                                break
                    if move == 'DOWN':
                        for j in range(x + 1, 4):
                            this_spot = self.board[j][y]
                            if spot == this_spot:
                                self.board[x][y] = 0
                                self.board[j][y] = this_spot * 2
                                self.score += this_spot * 2
                                break
                            if spot != 0:
                                break
                    if move == 'LEFT':
                        # for j in reversed(range(y - 1)):
                        for j in reversed(range(y)):
                            this_spot = self.board[x][j]
                            if spot == this_spot:
                                self.board[x][y] = 0
                                self.board[x][j] = this_spot * 2
                                self.score += this_spot * 2
                                break
                            if spot != 0:
                                break
                    if move == 'RIGHT':
                        for j in range(y + 1, 4):
                            this_spot = self.board[x][j]
                            if spot == this_spot:
                                self.board[x][y] = 0
                                self.board[x][j] = this_spot * 2
                                self.score += this_spot * 2
                                break
                            if spot != 0:
                                break

    def shift(self, move):
        for x in range(4):
            for y in range(4):
                spot = self.board[x][y]

                if spot != 0:
                    if move == 'UP':
                        for j in range(0, x):
                            this_spot = self.board[j][y]
                            if this_spot == 0:
                                self.board[x][y] = 0
                                self.board[j][y] = spot
                                break
                    if move == 'DOWN':
                        for j in reversed(range(x, 4)):
                            this_spot = self.board[j][y]
                            if this_spot == 0:
                                self.board[x][y] = 0
                                self.board[j][y] = spot
                                break
                    if move == 'LEFT':
                        for j in range(0, y):
                            this_spot = self.board[x][j]
                            if this_spot == 0:
                                self.board[x][y] = 0
                                self.board[x][j] = spot
                                break
                    if move == 'RIGHT':
                        for j in reversed(range(y, 4)):
                            this_spot = self.board[x][j]
                            if this_spot == 0:
                                self.board[x][y] = 0
                                self.board[x][j] = spot
                                break


    def insert_random(self):
        num = random.choice([2, 4])

        for _ in range(10):
            x = random.randint(0, 3)
            y = random.randint(0, 3)

            if self.board[x][y] == 0:
                self.board[x][y] = num
                return False

        for x in range(4):
            for y in range(4):
                if self.board[x][y] == 0:
                    self.board[x][y] = num
                    return False

        return True

