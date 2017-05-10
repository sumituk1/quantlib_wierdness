import pandas as pd
from mosaicsmartdata.common.read_config import *
import inspect

class Borg:
    _shared = {}

    def __init__(self):
        self.__dict__ = self._shared


class InstumentSingleton(Borg):
    def __init__(self):
        # this line plus the inheritance makes the magic happen
        # any class using that pattern will be a singleton
        super().__init__()
        configurator = Configurator()
        self.instrument_static_fname = configurator.get_config_given_key("instrument_static")

    def __call__(self, **kwargs):
        if 'data' not in self.__dict__:
            thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
            self.data = pd.read_csv(thisfiledir + '\\..\\configuration\\' + self.instrument_static_fname)
        out_data_df = self.data
        # now keep applying filter
        for k,v in kwargs.items():
            out_data_df = out_data_df[out_data_df[k] == v]
        if len(out_data_df) == 0:
            raise Exception("could find instrument static key %s"%list(kwargs.items())[0][1])

        return out_data_df.iloc[-1]

    def __str__(self):  # just for the illustration below, could be anything else
        return str(self.__dict__)

if __name__ == "__main__":
    instrument_static = InstumentSingleton()
    instr_static_df = instrument_static(sym='FGBLc1') #,date='2017.03.30')
    instr_static_df_2 = instrument_static(sym='US30YT=RR')  # ,date='2017.03.30')
    print(instr_static_df['duration'])
    print(instr_static_df_2['duration'])