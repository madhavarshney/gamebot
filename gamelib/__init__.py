from .database import Database
from .preferences import Preferences
from .session import SessionManager
from .registry import Registry

db = Database()
preferences = Preferences(db)
sessionManager = SessionManager(db)
registry = Registry()


def register(name, prefs=None):
    def decorator(func):
        registry.register(name, func)
        if prefs:
            preferences.register(name, prefs)
    return decorator
