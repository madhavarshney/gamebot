from tinydb import TinyDB, where
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

CachingMiddleware.WRITE_CACHE_SIZE = 0

class Database:
    def __init__(self):
        self.db = TinyDB('db.json', storage=CachingMiddleware(JSONStorage))
        self.players = self.db.table('players')

    def get_player_prefs(self, id):
        return self.players.get(where('id') == id)

    def set_player_prefs(self, id, data):
        self.players.upsert(data, where('id') == id)
