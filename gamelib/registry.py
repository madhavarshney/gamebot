class Registry:
    _registry: dict = None

    def __init__(self):
        self._registry = dict()

    def register(self, name, cls):
        self._registry[name] = cls

    def get(self, name):
        return self._registry.get(name)


registry = Registry()


def register(name):
    def decorator(func):
        registry.register(name, func)
    return decorator
