import sys
import logging
import asyncio

from abc import abstractmethod, ABC, ABCMeta

from discord.errors import NotFound

from . import sessionManager, preferences

loop = asyncio.get_event_loop()

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                asyncio.create_task(fn(*args, **kwargs))
            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = loop.call_later(wait, call_it)
        return debounced
    return decorator

class GameConfigError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class BaseBotApp(metaclass=ABCMeta):
    # __metaclass__ = ABCMeta

    def __init__(self, name: str, players):
        self.app_name = name
        self._players = players

    @abstractmethod
    async def begin(self, bot, message, player1, player2):
        '''
        Start an app or game.
        '''
        raise NotImplementedError

    @abstractmethod
    async def end(self):
        '''
        Stop a game.
        '''
        raise NotImplementedError

    @abstractmethod
    async def handle(self, event, **data):
        '''
        Handle an event

        react - On a reaction
        '''
        raise NotImplementedError

    # Utilities

    def preference(self, player, key):
        return preferences.get(player, self.app_name, key)

    def end_session(self):
        sessionManager.pop(self._players)

    def register_message(self, message):
        return sessionManager.register_message(message, self)

    def unregister_message(self, message):
        return sessionManager.unregister_message(message)


class MagicMessage:
    def __init__(self, channel):
        self.channel = channel
        self.message = None
        self.ended = False

    async def send(self, text):
        if not self.message:
            return await self._send(text)

        try:
            await self._edit(text)
        except NotFound:
            return await self._send(text)

        # Delete & resend message after a certain delay
        self._resend(text)

    async def cleanup(self):
        self.ended = True

        await self._delete()
        self._cancel()

    @debounce(5)
    async def _resend(self, text):
        if not self.ended:
            await self._delete()
            await self._send(text)

    async def _send(self, text):
        self.message = await self.channel.send(text)

    async def _edit(self, text):
        await self.message.edit(content=text)

    async def _delete(self):
        if self.message:
            try:
                await self.message.delete()
            except NotFound:
                pass

    def _cancel(self):
        try:
            self.delay.t.cancel()
        except AttributeError:
            pass


def setupLogger():
    logger = logging.getLogger('bot')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(message)s")
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
