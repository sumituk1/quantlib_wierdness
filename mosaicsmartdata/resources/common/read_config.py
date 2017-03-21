import os
import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../configuration")))
import configparser

config = configparser.ConfigParser()
pre = os.path.abspath(os.path.dirname(__file__) + '/' + '../configuration')
configFilePath = os.path.join(pre, 'config')
config.read(configFilePath)


# gets the value given a key for the 'DEFAULT' section
def get_config_given_key(key):
    return config['DEFAULT'][key]


# gets the value given a section/key
def get_data_given_section_and_key(section, key):
    return config[section][key]


# TODO: This code shouldn't be here.
# prepares the passed in ccy pair in the correct market convention order
def create_ccy_pair(_dom, _for):
    ccy_mkt_convention = config['FX']['fx_ccy_g10']
    str_list = list(ccy_mkt_convention.split(","))

    _dom_index = str_list.index(_dom)
    _for_index = str_list.index(_for)

    if _for_index > _dom_index:
        ccy = _for + "/" + _dom
    else:
        ccy = _dom + "/" + _for

    return ccy


if __name__ == "__main__":
    zz = get_data_given_section_and_key('FX', 'fx_ccy_g10')
    print(zz)
    print(create_ccy_pair("GBP", "JPY"))
