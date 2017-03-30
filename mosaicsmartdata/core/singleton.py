class Borg:
    _shared = {}

    def __init__(self):
        self.__dict__ = self._shared


class Singleton(Borg):
    def __init__(self):
        # this line plus the inheritance makes the magic happen
        # any class using that pattern will be a singleton
        super().__init__()

    def __call__(*args, **kwargs):
        if 'data' not in self.__dict__:
            pass  # load data if not already loaded

        # now do whatever you need to and return result
        return None

    def __str__(self):  # just for the illustration below, could be anything else
        return str(self.__dict__)
    