from collections import defaultdict

from .database import Database

class Preferences:
    def __init__(self, db: Database):
        self.db = db
        self.available = {}

    def get(self, player, app, key):
        prefs = self.get_all(player)

        if app in prefs and key in prefs[app]:
            return prefs[app][key]

        return None

    def get_all(self, player):
        return self.db.get_player_prefs(player.id) or {}

    def get_all_for_app(self, player, app):
        return self.get_all(player.id).get(app) or {}

    def set(self, player, app: str, key: str, value: str):
        if not self.exists(app, key):
            raise KeyError

        prefs = self.db.get_player_prefs(player.id) or {'id': player.id}
        prefs = defaultdict(dict, prefs)
        prefs[app][key] = value
        self.db.set_player_prefs(player.id, dict(prefs))

    def exists(self, app: str, key: str):
        return app in self.available and key in self.available[app]

    def register(self, app, settings):
        self.available[app] = settings

    def app(self, app):
        return lambda player, key: self.get(player, app, key)
