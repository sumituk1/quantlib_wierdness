import pandas as pd
from mosaicsmartdata.common.read_config import *

class Borg:
    _shared = {}

    def __init__(self):
        self.__dict__ = self._shared


class InstumentSingleton(Borg):
    def __init__(self):
        # this line plus the inheritance makes the magic happen
        # any class using that pattern will be a singleton
        super().__init__()
        self.instrument_static_fname = get_config_given_key("instrument_static")

    def __call__(self, **kwargs):
        if 'data' not in self.__dict__:
            self.data = pd.read_csv(self.instrument_static_fname)
        out_data_df = self.data
        # now keep applying filter
        for k,v in kwargs.items():
            out_data_df = out_data_df[out_data_df[k] == v]
        return out_data_df

    def __str__(self):  # just for the illustration below, could be anything else
        return str(self.__dict__)

if __name__ == "__main__":
    instrument_static = InstumentSingleton()
    instr_static_df = instrument_static(sym='FGBLc1',date='2017.03.30')
    print(instr_static_df)