'''Provides various single-curve based functionalities like:
1. Construct OIS curve - construct_OIS_curve()
2. Construct a OIS discount/ libor forecasting curve - construct_forecast_curve()
3. get the forward rate between start & end_date - get_rate()
4. read the Data Extractor.xlsx to get the swap rates and OIS rates -  read_usd_libor_data()'''
import datetime as dt

import numpy as np
import pandas as pd
from QuantLib import *

from mosaicsmartdata.common.constants import BootStrapMethod
from mosaicsmartdata.common.constants import Currency
from mosaicsmartdata.common.constants import HolidayCities
from mosaicsmartdata.common.quantlib import fixed_bond
from mosaicsmartdata.common.quantlib.curve.usdois import USDOIS
from mosaicsmartdata.common.quantlib.fixed_bond import pydate_to_qldate


# class CacheBorg:
#     _shared = {}
#
#     def __init__(self):
#         self.__dict__ = self._shared
#
# class Cache(CacheBorg):
#     def __init__(self):
#         super().__init__()
#         if 'data' not in self.__dict__:
#             self.data =[]

def construct_OIS_curve(usd_ois_quotes_, today = None, holiday_cities = HolidayCities.USD, ccy = None):
    '''
    :param usd_ois_quotes: a dict where the key is the tuple (start date, end date) and the value is the quote
    We assume the dates in the quotes are strictly ordered
    :return: a curve object
    '''
    # cache the in-args:
    # if True:
    #     cache = Cache()
    #     cache.data.append((usd_ois_quotes_, today , holiday_cities, ccy))
    # create the OIS curve


    usd_ois_quotes = [(q[0],q[1],q[2],q[3]) for q in usd_ois_quotes_]
    us_calendar = UnitedStates()

    first_data_date = [key for key in usd_ois_quotes][0][0]
    if today is None:
        valuation_date = first_data_date
    else:
        valuation_date = today

    usd_ois = USDOIS(pydate_to_qldate(valuation_date),
                     us_calendar, holiday_cities) # Pass in the Trade date- not the settle_date
    try:
        ##Add a dummy deposit - didn't help at all
        # if today is not None and first_data_date != today:
        #     fake_first_quote = (today, first_data_date, usd_ois_quotes[0][2], 'DUMMY')
        #     usd_ois_quotes = [fake_first_quote] + usd_ois_quotes

        usd_ois.create_deposit_rates(usd_ois_quotes)
        # ois_rates = usd_ois_quotes
        usd_ois.create_ois_swaps(usd_ois_quotes)
        usd_ois.source_data = usd_ois_quotes_ # for later inspection
        usd_ois.source_data_with_dummy = usd_ois_quotes
        usd_ois.ccy = ccy
    except Exception as e:
        pass

    return usd_ois

'''Bootstraps the OIS discount curve from OIS rates & deposit rates and then the forecast curve.
Returns the USDOIS object'''


def construct_forecast_curve(usd_ois_quotes_, usd_3m_rates, holiday_cities=HolidayCities.USD, ccy=None):
    usd_ois = construct_OIS_curve(usd_ois_quotes_, holiday_cities, ccy)

    # bootstrap the forecast curve
    usd_ois.bootstrap_usd_ois_3M_curve(usd_3M_swap_rates=usd_3m_rates,
                                       discountCurve=usd_ois.ois_curve_c,
                                       bootStrapMethod=BootStrapMethod.PiecewiseFlatForward)
    return usd_ois


''' Gets the forward rate given a curve object'''


def get_rate(ois_curve: USDOIS, start_date, end_date, daycount=Actual360()):
    '''
    :param curve:
    :param start_date:
    :param end_date:
    :param kwargs
    :return: a double: value of the rate implied by the curve between the two dates
    '''
    # c = ois_curve.ois_curve_c
    if pydate_to_qldate(start_date) < pydate_to_qldate(ois_curve.valuationDate):
        raise ValueError('Start of date range is before curve valuation date')
    return ois_curve.ois_curve_c.forwardRate(pydate_to_qldate(start_date),
                                             pydate_to_qldate(end_date),
                                             daycount, Simple).rate() * 100


''' Gets the discount_factor given a curve and start and end_date'''


def discounting_factor(ois_curve, date_1, date_2=None, one_pre_spot=False):
    '''
    Returns the discounting factor from the second date onto the first
    :param curve:
    :param start_date:
    :param end_date:
    :return: discounting factor
    '''
    if date_2 is None:
        valuation_date = ois_curve.valuationDate
        end_date = date_1
    else:
        valuation_date = date_1
        end_date = date_2

    end_date = pydate_to_qldate(end_date)
    valuation_date = pydate_to_qldate(valuation_date)

    if valuation_date > end_date:
        if one_pre_spot:  # use this flag to extend the USD OIS curve to 0 at pre-spot, as we only care about yield differential anyway
            return 1.0
        else:  # at least make sure the dates are in proper order
            end_date, valuation_date = valuation_date, end_date
            invert = True
    elif valuation_date == end_date:
        return 1.0
    else:
        invert = False

    dt = ois_curve.calendar.businessDaysBetween(valuation_date, end_date) / 360
    if dt < 0:
        pass
    # print(valuation_date,end_date)
    dr = get_rate(ois_curve, valuation_date, end_date)
    # print('*** success!!! ***')
    df = np.exp(- dr * dt)

    if invert:
        df = 1 / df
    # print(dr)
    return df


'''Creates a curve object from discount factors'''


def curve_from_disc_factors(disc_factors, calendar=None, ccy=None):
    '''
    Constructs a discounting curve from a list of discount factors
    :param disc_factors: list of tuples (disc_factor, start_date, end_date)
    :param kwargs: Extra stuff like daycount conventions etc
    :return:
    '''
    if calendar == None:
        # TODO: guess calendar from currency?
        calendar = UnitedStates()
    rates_list = []
    for start_date, end_date, disc_factor, tenor in disc_factors:
        if start_date is None or end_date is None:
            pass
        try:
            if start_date > end_date:  # for ON, TN tenors
                start_date, end_date = end_date, start_date
                disc_factor = 1 / disc_factor
        except:
            pass
        dt = calendar.businessDaysBetween(pydate_to_qldate(start_date),
                                          pydate_to_qldate(end_date)) / 360
        dr = -(1 / dt) * np.log(disc_factor)
        rates_list.append((start_date, end_date, dr, tenor))  # disc_factor))

    # sort the tenors:
    # ontn = [x for x in rates_list if x[3] == 'ONTN']
    # tn = [x for x in rates_list if x[3] == 'TN']
    # rest = [x for x in rates_list if x[3] not in ['ONTN','TN']]
    # rest.sort(key = lambda x: x[1])
    # rates_list = ontn + tn + rest

    # if ccy is not None:
    #     with open(ccy + '_curve.pickle', 'wb') as f:
    #         cloudpickle.dump(rates_list, f)
    # print(rates_list)
    # TODO: uncomment!
    # curve = None
    curve = construct_OIS_curve(rates_list, ccy=ccy)
    return curve


''' Reads a eikon excel file to extract the rates data'''


def read_usd_libor_data(file, sheet="USD Swaps"):
    ccy = sheet.split(" ")[0]
    ois_df = pd.DataFrame(data=None)
    if ccy == Currency.USD.value:
        libor_rates_df = pd.read_excel(file,
                                       index_col=0,
                                       sheetname=sheet,
                                       header=0,
                                       skiprows=3,
                                       parse_cols="B:V").dropna(how='all')

        usd_ois_basis_df = pd.read_excel(file,
                                         index_col=0,
                                         sheetname=sheet,
                                         header=0,
                                         skiprows=3,
                                         parse_cols="X:AM").dropna(how='all')
        for cols in usd_ois_basis_df.columns.values:
            ois_df[cols] = libor_rates_df[cols] - usd_ois_basis_df[cols] / 100
    elif ccy == Currency.EUR.value:
        libor_rates_df = pd.read_excel(file,
                                       index_col=0,
                                       sheetname=sheet,
                                       header=0,
                                       skiprows=3,
                                       parse_cols="B:Y").dropna(how='all')

        usd_ois_basis_df = pd.read_excel(file,
                                         index_col=0,
                                         sheetname=sheet,
                                         header=0,
                                         skiprows=3,
                                         parse_cols="AA:BB").dropna(how='all')
        for cols in usd_ois_basis_df.columns.values:
            ois_df[cols] = usd_ois_basis_df[cols]
    else:
        raise ValueError('read_libor data from excel not implemented for:' + ccy)

    return libor_rates_df, ois_df


"""Converts a dataset to a list format that QL can understand"""
def convert_df_to_ql_list(ql_date, tenor_list, rates, include_months=True):
    # get the header list
    # tenor_list = []
    # [tenor_list.append(x) for x in tenor_list]
    #
    # # get the most recent yield curve
    # rates = []
    # [rates.append(x) for x in rates]
    if isinstance(ql_date,dt.datetime):
        ql_date = fixed_bond.pydate_to_qldate(ql_date)

    out_list = []
    # finally merge the two lists
    for idx in range(len(tenor_list)):

        if include_months:
            if tenor_list[idx][-1] == "M":
                ed = ql_date + Period(int(tenor_list[idx][:-1]), Months)
                out_list.append(tuple((ql_date, ed, rates[idx], tenor_list[idx])))
            elif tenor_list[idx][-1] == "W":
                ed = ql_date + Period(int(tenor_list[idx][:-1]), Weeks)
                out_list.append(tuple((ql_date, ed, rates[idx], tenor_list[idx])))
            elif tenor_list[idx][-1] == "Y":
                ed = ql_date + Period(int(tenor_list[idx][:-1]), Years)
                out_list.append(tuple((ql_date, ed, rates[idx], tenor_list[idx])))
        else:
            # todo: current implementation only takes 3m libor swap rates >= 1y
            if tenor_list[idx][-1] == "Y":
                out_list.append(tuple((rates[idx], int(tenor_list[idx][:-1]))))

    return out_list


if __name__ == "__main__":
    ## test 1
    spot_date = dt.date(2017, 9, 19)
    maturity_dates = [spot_date + dt.timedelta(days=30 * i) for i in range(1, 4)]
    ois_rates = [1.1450, 1.1490, 1.160]
    labels = ['1M', '2M', '3M']
    rate_list = []
    for md, rate, label in zip(maturity_dates, ois_rates, labels):
        rate_list.append([spot_date, md, rate, label])

    curve = construct_OIS_curve(rate_list)
    r = get_rate(curve, spot_date, maturity_dates[0])
    print(r)

    ######### test 2  #######
    libor_rates_df, ois_rates_df = read_usd_libor_data("..\\..\\..\\resources\\Data extractor.xlsx",sheet="EUR Swaps")
    libor_column = libor_rates_df.columns.values
    ois_column = ois_rates_df.columns.values
    # convert dataframe to a list that QL can understand
    for libor_rate, ois_rate \
            in zip(libor_rates_df.values,
                   ois_rates_df.values):
        libor_rate_ql = convert_df_to_ql_list(libor_column, libor_rate)
        ois_rate_ql = convert_df_to_ql_list(ois_column, ois_rate)

    print(libor_rate_ql)
    print(ois_rate_ql)
