import os
import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../configuration")))
# import configparser
from mosaicsmartdata.core.config_parser import *


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

        if 'config' not in self.__dict__:
            self.config = ConfigParser()
            pre = os.path.abspath(os.path.dirname(__file__) + '/' + '../configuration')
            if fname is None:
                configFilePath = os.path.join(pre, 'config')
            else:
                configFilePath = os.path.join(pre, fname)
            # load the configuration data into memory
            self.config.read(configFilePath)

    def __call__(self, fname):
        pass

    # gets the value given a key for the 'DEFAULT' section
    def get_config_given_key(self, key):
        return self.config['DEFAULT'][key]

    # gets the value given a section/key
    def get_data_given_section_and_key(self, section, key):
        return self.config[section][key]

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
    config_1 = Configurator('config')
    zz = config_1.get_data_given_section_and_key('FX', 'fx_ccy_g10')
    print(zz)
    config_2 = Configurator('config')
    print(config_2.create_ccy_pair("GBP", "JPY"))
    zz = config_2.get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
    print(zz)
    # config.read("C:\\Users\\Sumit Sengupta\\Documents\msq-domain\\mosaicsmartdata\\configuration\\config")
    # zz = get_data_given_section('USD_GovtBond_Hedge_Mapper')
    # print(zz)
