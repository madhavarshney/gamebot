import sys
import logging

from abc import abstractmethod, ABC, ABCMeta

from . import sessionManager

class BotApp(metaclass=ABCMeta):
    # __metaclass__ = ABCMeta

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
    async def notify(self, event, **data):
        '''
        Handle an event

        react - On a reaction
        '''
        raise NotImplementedError

    # Utilities

    def end_session(self, player1, player2):
        sessionManager.pop(player1, player2)


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
