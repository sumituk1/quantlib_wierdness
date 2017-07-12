import inspect, os, sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../configuration")))
# import configparser
from mosaicsmartdata.core.config_parser import *
import mosaicsmartdata
import logging
import glob

class Borg:
    _shared = {}

    def __init__(self):
        self.__dict__ = self._shared


''' Singleton Config class. Note that its assumed a single instance of QC will run per config'''


class Configurator(Borg):
    def __init__(self, fname=None):
        # this line plus the inheritance makes the magic happen
        # any class using that pattern will be a singleton
        super().__init__()

        if fname not in self.__dict__:#'config' not in self.__dict__:
            # have to do this weird scan so the test runs both in pyb and pycharm
            root_location = mosaicsmartdata.__path__
            if len(root_location) > 1:
                root_location = [x for x in root_location if 'msq-domain' in x]
            pre = root_location[0] + '/configuration'
            if fname is None:
                configFilePath = os.path.join(pre, 'config.csv')
            else:
                configFilePath = os.path.join(pre, fname)
            logging.getLogger(__name__).info('Trying to read configs from ' + configFilePath)
            logging.getLogger(__name__).info('glob.glob resolves that to '.join(glob.glob(configFilePath)))
            # load the configuration data into memory

            self.config = ConfigParser()
            self.config.read(configFilePath)

    def __call__(self, fname):
        pass

    # gets the value given a key for the 'DEFAULT' section
    def get_config_given_key(self, key):
        return self.config['DEFAULT'][key]

    # gets the value given a section/key
    def get_data_given_section_and_key(self, section, key):
        return self.config[section][key]

    # goes through the config stack and searches for the section which matches the partial_name
    # and completely matches the val passed in
    def get_section_given_item_val(self, val, partial_section_name):
        for k1, v1 in self.config.items():
            for k2, v2 in self.config[k1].items():
                if (str.upper(partial_section_name) in str.upper(k1)) \
                        and (val in v2.split(',')):
                    return k1
        return None

    # gets the value given a section
    def get_data_given_section(self, section):
        # return dict(config.items(section))
        return dict(self.config.options(section, no_defaults=True))

    # TODO: This code shouldn't be here.
    # prepares the passed in ccy pair in the correct market convention order
    def create_ccy_pair(self, _dom, _for):
        ccy_mkt_convention = self.config['FX']['fx_ccy_g10']
        str_list = list(ccy_mkt_convention.split(","))

        _dom_index = str_list.index(_dom)
        _for_index = str_list.index(_for)

        if _for_index > _dom_index:
            ccy = _for + "/" + _dom
        else:
            ccy = _dom + "/" + _for

        return ccy


if __name__ == "__main__":
    config_1 = Configurator('config.csv')
    zz = config_1.get_data_given_section_and_key('FX', 'fx_ccy_g10')
    print(zz)
    config_2 = Configurator('config.csv')
    print(config_2.create_ccy_pair("GBP", "JPY"))
    zz = config_2.get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
    print(zz)
    zz = config_2.get_section_given_item_val("IT","GovtBond_listed_Hedge_Mapper")
    print(zz)
    # config.read("C:\\Users\\Sumit Sengupta\\Documents\msq-domain\\mosaicsmartdata\\configuration\\config")
    # zz = get_data_given_section('USD_GovtBond_Hedge_Mapper')
    # print(zz)
