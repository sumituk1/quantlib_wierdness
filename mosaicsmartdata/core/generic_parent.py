import datetime as dt
import numpy as np
from mosaicsmartdata.common import read_config
from mosaicsmartdata.core.repo_singleton import *
from mosaicsmartdata.common.quantlib.bond.bond_forward_price import *
from mosaicsmartdata.common.quantlib.bond.bond_price import *
import mosaicsmartdata.common.quantlib.bond.fixed_bond as bond
from mosaicsmartdata.common.constants import *


class GenericParent:
    def __init__(self, *args, **kwargs):
        if len(kwargs):
            raise ValueError('Unknown arguments:', kwargs)

    def apply_kwargs(self, goodargs, kwargs):
        # print('Entering apply_kwargs', self, goodargs, kwargs)

        other_kwargs = {key: value for key, value in kwargs.items() if key not in goodargs}
        good_kwargs = {key: value for key, value in kwargs.items() if key in goodargs}

        for key, value in good_kwargs.items():
            self.__dict__[key] = value

        return other_kwargs

    def check_values(self, names):
        for x in names:
            if self.__dict__[x] is None:
                raise ValueError(x + ' must be specified')

    def __str__(self):
        my_string = str(type(self)) + ' : '
        for key, value in self.__dict__.items():
            my_string = my_string + ', ' + key + ' = ' + str(value)
        my_string = my_string.replace(': ,', ': ')
        return my_string