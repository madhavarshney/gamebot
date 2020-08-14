from collections import defaultdict

from .database import Database

class Preferences:
    def __init__(self, db: Database):
        self.db = db

    def get(self, player):
        return self.db.get_player_prefs(player.id) or {}

    def set(self, player, app, key, value):
        prefs = defaultdict(dict, self.db.get_player_prefs(player.id) or {'id': player.id})
        prefs[app][key] = value
        self.db.set_player_prefs(player.id, prefs)
