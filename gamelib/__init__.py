from .database import Database
from .preferences import Preferences
from .session import SessionManager
from .registry import registry, register

db = Database()
preferences = Preferences(db)
sessionManager = SessionManager(db)
