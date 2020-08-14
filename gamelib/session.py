from .database import Database

class SessionManager:
    def __init__(self, db: Database):
        self.db = db
        self._sessions = dict()
        self._players = dict()
        self._messages = dict()


    def add(self, player1, player2, app):
        if self.get(player1, player2):
            return False

        sessionId = SessionManager.id(player1, player2)
        self._sessions[sessionId] = app

        for player in [player1, player2]:
            self._players[player.id] = app

        return True


    def pop(self, player1, player2):
        try:
            sessionId = SessionManager.id(player1, player2)
            app = self._sessions.pop(sessionId)

            if app:
                for player in set([player1, player2]):
                    self._players.pop(player.id)

                return app

            return None
        except KeyError as e:
            return None


    def get(self, player1, player2):
        try:
            sessionId = SessionManager.id(player1, player2)
            return self._sessions[sessionId]
        except KeyError:
            return None


    def get_player_session(self, player):
        try:
            return self._players[player.id]
        except KeyError:
            return None


    def register_message(self, message, app):
        self._messages[message.id] = app


    def unregister_message(self, message, app):
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
    def id(player1, player2):
        return frozenset([player1.id, player2.id])
