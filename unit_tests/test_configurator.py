from unittest import TestCase
from mosaicsmartdata.common.read_config import Configurator


class TestConfigurator(TestCase):
    # Test for Trade json convertor
    def test_case_1(self):
        config_1 = Configurator('config')
        zz = config_1.get_data_given_section_and_key('FX', 'fx_ccy_g10')
        self.assertEquals(zz, 'EUR,GBP,AUD,NZD,USD,CAD,CHF,NOK,SEK,JPY', msg=None)
        config_2 = Configurator('config')
        zz = config_2.create_ccy_pair("GBP", "JPY")
        self.assertEquals(zz, 'JPY/GBP', msg=None)
        zz = config_2.get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
        self.assertEquals(zz, '16:30:00', msg=None)
        zz= config_2.get_data_given_section('USD_GovtBond_OTC_Hedge_Mapper')
        tenor = 7
        # extract the tenors - first 2 config are hedge specific different config
        tenors_list = sorted([float(x) for x in (sorted([x for x in list(zz.keys())])[:-2])])
        # get the hedge sym(s)
        hedge_sym_arr = zz[str([x for x in tenors_list if tenor >= x][-1]).rstrip('0').rstrip('.')]
        hedge_sym_arr = hedge_sym_arr.split(',')
        self.assertEquals(hedge_sym_arr,['US5YT=RR','US10YT=RR'],msg=None)

    def test_case_2(self):

        config_2 = Configurator('config_hedge_test_case_5')
        zz = config_2.get_data_given_section('USD_GovtBond_OTC_Hedge_Mapper')
        tenor = 7
        # extract the tenors - first 2 config are hedge specific different config
        tenors_list = sorted([float(x) for x in (sorted([x for x in list(zz.keys())])[:-2])])
        # get the hedge sym(s)
        hedge_sym_arr = zz[str([x for x in tenors_list if tenor >= x][-1]).rstrip('0').rstrip('.')]
        hedge_sym_arr = hedge_sym_arr.split(',')
        self.assertEquals(hedge_sym_arr, ['US10YT=RR', 'US30YT=RR'], msg=None)

    def test_case_3(self):
        config_2 = Configurator('config')
        zz = config_2.get_section_given_item_val("IT", "GovtBond_listed_Hedge_Mapper")
        self.assertEquals(zz,'EGB_peri_GovtBond_LISTED_Hedge_Mapper', msg=None)
        zz = config_2.get_section_given_item_val("IT", "GovtBond_cash_Hedge_Mapper")
        self.assertEquals(zz, None, msg=None)
        zz = config_2.get_section_given_item_val("IT", "GovtBond_OTC_Hedge_Mapper")
        self.assertEquals(zz, 'EGB_peri_GovtBond_OTC_Hedge_Mapper', msg=None)