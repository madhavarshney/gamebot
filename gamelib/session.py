from .database import Database

class SessionManager:
    def __init__(self, db: Database):
        self.db = db
        self._sessions = dict()
        self._players = dict()
        self._messages = dict()


    def add(self, players, app):
        if self.get(players):
            return False

        sessionId = SessionManager.hash(players)
        self._sessions[sessionId] = app

        for player in players:
            self._players[player.id] = app

        return True


    def pop(self, players):
        try:
            sessionId = SessionManager.hash(players)
            app = self._sessions.pop(sessionId)

            if app:
                for player in set(players):
                    self._players.pop(player.id)

                return app

            return None
        except KeyError as e:
            return None


    def get(self, players):
        try:
            sessionId = SessionManager.hash(players)
            return self._sessions[sessionId]
        except KeyError:
            return None


    async def killall(self):
        for app in self._sessions.values():
            await app.end()

        self._sessions = {}
        self._players = {}


    def get_player_session(self, player):
        try:
            return self._players[player.id]
        except KeyError:
            return None


    def register_message(self, message, app):
        self._messages[message.id] = app


    def unregister_message(self, message):
        try:
            self._messages.pop(message.id)
            return True
        except KeyError:
            return False


    def get_message_session(self, message):
        try:
            return self._messages[message.id]
        except KeyError:
            return None


    @staticmethod
    def hash(players):
        return frozenset(map(lambda p: p.id, players))
