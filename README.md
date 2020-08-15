# Game Bot

A discord bot with a bunch of prebuilt games, and a framework to create your own games.


## Write your own game

So, you want to make your own game, right? Well, that's great! Get started by creating a file `games/[game_name].py` where `[game_name]` is any name you like. To load this game, add an import statement in `games/__init__.py`.

```py
from .[game_name] import *
```

Make sure to replace `[game_name]` with the name of your game!

### Basic Example

Start by importing the required libs, and creating a class:

```py
from gamelib import register
from gamelib.utils import BaseBotApp, GameConfigError

GAME_NAME = 'demo'

@register(name=GAME_NAME)
class Demo(BaseBotApp):
    pass
```

So far, this game doesn't do anything, and it also won't run. Let's add the required methods:

```py
class Demo(BaseBotApp):
    def __init__(self, bot, players, channel):
        if len(players) > 1:
            raise GameConfigError('This game can only be played by one person!')

        super().__init__(GAME_NAME, players)

        self.channel = channel
        self.player = players[0]
        self.message = None
        self.reaction = None
```

Add begin and end handlers:

```py
    async def begin(self):
        await self.update_message()
        self.register_message(self.message)

    async def end(self):
        self.unregister_message(self.message)
        self.end_session()
```

Render the message:

```py
    async def update_message(self):
        if self.message:
            await self.message.edit(content=self.render())
        else:
            self.message = await self.channel.send(content=self.render())

    def render(self):
        if self.reaction:
            return f'{self.player.mention} reacted with {self.reaction.emoji}'
        else:
            return 'Try reacting to this message!'
```

Add some event handling:

```py
    async def handle(self, event, **data):
        if event == 'reaction':
            user = data.get('user')
            reaction = data.get('reaction')

            self.reaction = reaction

            await reaction.remove(user)
            await self.update_message()
```

Try this game! In discord, send `g!play demo`. You should see a message saying:

> Try reacting to this message!

Add a reaction, and make sure the message update. It should show the emoji that you reacted. When you're done "playing" this game, send `g!end` to end the game.

### Final code

```py
from gamelib import register
from gamelib.utils import BaseBotApp, GameConfigError

GAME_NAME = 'demo'

@register(name=GAME_NAME)
class Demo(BaseBotApp):
    def __init__(self, bot, players, channel):
        if len(players) > 1:
            raise GameConfigError('This game can only be played by one person!')

        super().__init__(GAME_NAME, players)

        self.channel = channel
        self.player = players[0]
        self.message = None
        self.reaction = None

    async def begin(self):
        await self.update_message()
        self.register_message(self.message)

    async def end(self):
        self.unregister_message(self.message)
        self.end_session()

    async def handle(self, event, **data):
        if event == 'reaction':
            user = data.get('user')
            reaction = data.get('reaction')

            self.reaction = reaction

            await reaction.remove(user)
            await self.update_message()

    async def update_message(self):
        if self.message:
            await self.message.edit(content=self.render())
        else:
            self.message = await self.channel.send(content=self.render())

    def render(self):
        if self.reaction:
            return f'{self.player.mention} reacted with {self.reaction.emoji}'
        else:
            return 'Try reacting to this message!'
```
