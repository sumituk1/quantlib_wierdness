from unittest import TestCase
from mosaicsmartdata.core.singleton import Singleton


class TestSingleton(TestCase):

    def test_case_1(self):
        a = Singleton()
        a.a = 1

        b = Singleton()
        self.assertEqual(b.a, 1)
        self.assertEqual(b.__dict__, {'a': 1})
