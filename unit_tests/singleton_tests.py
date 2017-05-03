from unittest import TestCase
# from mosaicsmartdata.core.singleton import Singleton

class Borg:
    _shared = {}

    def __init__(self):
        self.__dict__ = self._shared


class Singleton(Borg):
    def __init__(self):
        # this line plus the inheritance makes the magic happen
        # any class using that pattern will be a singleton
        super().__init__()

    def __call__(self,*args, **kwargs):
        if 'data' not in self.__dict__:
            pass  # load data if not already loaded

        # now do whatever you need to and return result
        return None

    def __str__(self):  # just for the illustration below, could be anything else
        return str(self.__dict__)

class TestSingleton(TestCase):

    def test_case_1(self):
        a = Singleton()
        a.a = 1

        b = Singleton()
        self.assertEqual(b.a, 1)
        self.assertEqual(b.__dict__, {'a': 1})
