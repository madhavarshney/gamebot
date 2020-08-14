class Registry:
    _registry: dict = None

    def __init__(self):
        self._registry = dict()

    def register(self, name, cls):
        self._registry[name] = cls

    def get(self, name):
        return self._registry.get(name)

    def all(self):
        return self._registry.keys()
