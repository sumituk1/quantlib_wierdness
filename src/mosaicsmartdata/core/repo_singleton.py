import pandas as pd
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.common.constants import *
import inspect
import datetime as dt
pd.options.mode.chained_assignment = None  # default='warn'
class Borg:
    _shared = {}

    def __init__(self):
        self.__dict__ = self._shared


class RepoSingleton(Borg):
    def __init__(self):
        # this line plus the inheritance makes the magic happen
        # any class using that pattern will be a singleton
        super().__init__()
        configurator = Configurator()
        self.repo_fname = configurator.get_config_given_key("repo")

    def __call__(self, **kwargs):
        if 'data' not in self.__dict__:
            thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
            self.data = pd.read_csv(thisfiledir + '/../configuration/' + self.repo_fname, header=0)
        df_dict = dict()
        out_data_df = self.data[1:]
        out_data_us = out_data_df.iloc[:,:2]
        out_data_us.iloc[:, 0] = pd.to_datetime(out_data_us.iloc[:, 0]) # convert to datetime
        df_dict['USD'] = out_data_us.sort_values(by=out_data_us.columns[0], ascending=False)
        out_data_eur = out_data_df.iloc[:, 2:4]
        out_data_eur.iloc[:, 0] = pd.to_datetime(out_data_eur.iloc[:, 0]) # convert to datetime
        df_dict['EUR'] = out_data_eur.sort_values(by=out_data_eur.columns[0], ascending=False)
        out_data_gbp = out_data_df.iloc[:, 4:]
        out_data_gbp.iloc[:, 0] = pd.to_datetime(out_data_gbp.iloc[:, 0]) # convert to datetime
        df_dict['GBP'] = out_data_gbp.sort_values(by=out_data_gbp.columns[0], ascending=False)
        # now keep applying filter

        out_data_ccy_filt = df_dict[kwargs["ccy"]] # <- a dataframe for a ccy
        out_data = out_data_ccy_filt[out_data_ccy_filt.iloc[:, 0] <= kwargs["date"]]
        if len(out_data) == 0:
            # input date is before the min date in the stored data
            out_data = out_data_ccy_filt.iloc[-1,:]
            output = float(out_data.values[1])
        else:
            output = float(out_data.iloc[0, :].values[1])

        if output is None:
            raise Exception("could find repo for %s"%list(kwargs.items())[0][1])

        return output

    def __eq__(self, other):
        # it's a singleton, so checking class is enough
        return self.__class__ == other.__class__

    def __setstate__(self, state):
        pass

            # def __str__(self):  # just for the illustration below, could be anything else
    #     return str(self.__dict__)

if __name__ == "__main__":
    repo = RepoSingleton()
    data = repo(ccy=Currency.EUR, date=dt.datetime(2017,3,10))
    print(data)
    # instr_static_df_2 = instrument_static(sym='US30YT=RR')  # ,date='2017.03.30')
    # print(instr_static_df['duration'])
    # print(instr_static_df_2['duration'])