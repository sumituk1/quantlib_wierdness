import datetime as dt

import numpy as np
from QuantLib import *

from mosaicsmartdata.common.quantlib.bond import fixed_bond
from mosaicsmartdata.common.quantlib.bond import fixed_bond
from mosaicsmartdata.common.quantlib.curve.usdois import USDOIS

''' Class to contain a calibrated USD 3m libor curve with OIS discounting'''


# class USDOIS:
#     # today = Date_todaysDate()
#
#     def __init__(self, *args):
#         self.__ff_local = FedFunds()  # We need an instance of the FF class which doesn;t need a forecast curve
#         self.__calendar = UnitedStates()  # calendar class
#         self.__valuationDate = Date_todaysDate()
#         self.__ois_curve_c = None  ## Holds the bootstrapped OIS curve
#
#         if len(args) == 0:
#             self.__valuationDate = Date_todaysDate()
#             Settings.instance().evaluationDate = Date_todaysDate()
#         else:
#             self.__valuationDate = args[0]
#             Settings.instance().evaluationDate = self.__valuationDate
#             calendar = args[1]
#             # self.usd_libor = USDLibor()
#
#     # Finally, we add OIS quotes up to 30 years.
#     def create_ois_swaps(self, ois_swap_rates):
#
#         helpers = [DatedOISRateHelper(start_date, end_date, QuoteHandle(SimpleQuote(rate / 100)), self.__ff_local)
#                    for start_date, end_date, rate in [tuple((fixed_bond.pydate_to_qldate(key[0]),
#                                                              fixed_bond.pydate_to_qldate(key[1]),
#                                                              ois_swap_rates[key])) for key
#                                                       in ois_swap_rates]]
#         # for start_date, end_date, rate in ois_swap_rates]
#         self.__ois_curve_c = PiecewiseLogCubicDiscount(0, self.__calendar, helpers, Actual365Fixed())
#         self.__ois_curve_c.enableExtrapolation()
#         # return ois_curve_c
#
#     # The curve is an instance of PiecewiseLogCubicDiscount (corresponding to the PiecewiseYield-
#     # Curve<Discount,LogCubic> class in C++;
#     def bootstrap_usd_ois_3M_curve(self,
#                                    usd_3M_swap_rates,
#                                    discountCurve,
#                                    bootStrapMethod=BootStrapMethod.PiecewiseLogCubicDiscount):
#
#         discount_curve = RelinkableYieldTermStructureHandle()
#         discount_curve.linkTo(discountCurve)
#         helpers = [SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
#                                   Period(tenor, Years),
#                                   TARGET(),
#                                   Semiannual,
#                                   Unadjusted,
#                                   Thirty360(Thirty360.BondBasis),
#                                   Euribor3M(),
#                                   QuoteHandle(),
#                                   Period(0, Days),
#                                   discount_curve)
#                    for rate, tenor in usd_3M_swap_rates]
#
#         if bootStrapMethod == BootStrapMethod.PiecewiseLogCubicDiscount:
#             self.usd_3M_c = PiecewiseLogCubicDiscount(0, TARGET(), helpers, Actual365Fixed())
#         elif bootStrapMethod == BootStrapMethod.PiecewiseFlatForward:
#             self.usd_3M_c = PiecewiseFlatForward(0, TARGET(), helpers, Actual365Fixed())
#
#         # Also, we enable extrapolation beyond the maturity of the last helper; that is mostly
#         # for convenience as we retrieve rates to plot the curve near its far end.
#         self.usd_3M_c.enableExtrapolation()
#
#         # This is a test function
#
#         # def test_usd_3m_bootstrap():
#         #     usd_ois = USDOIS(Date(15, 5, 2017))  # Pass in the Trade date- not the settle_date
#         #
#         #     ois_swap_rates = [(1.189, (1, Years)), (1.345, (2, Years)), (1.477, (3, Years)),
#         #                       (1.5907, (4, Years)), (1.681, (5, Years)), (1.758, (6, Years)),
#         #                       (1.8258, (7, Years)), (1.879, (8, Years)), (1.9301, (9, Years)),
#         #                       (1.9765, (10, Years)), (2.007, (12, Years)), (2.034, (15, Years)),
#         #                       (2.053, (20, Years)), (2.071, (25, Years)), (2.085, (30, Years))]
#         #
#         #     # create the OIS curve
#         #     ois_curve = usd_ois.create_ois_swaps(ois_swap_rates)
#         #
#         #     # usd_swap_3M_rates = [(1.356, (12,Months)), (1.5312, (2,Years)), (1.6421, (3,Years)),
#         #     #                      (1.7677, (4,Years)), (1.8727, (5,Years)), (1.9526, (6,Years)),
#         #     #                      (2.0228, (7,Years)), (2.0719, (8,Years)), (2.128, (9,Years)),
#         #     #                      (2.205, (10,Years)), (2.225, (11,Years)), (2.262, (12,Years)),
#         #     #                      (2.297, (13,Years)), (2.322, (14,Years)), (2.346, (15,Years)),
#         #     #                      (2.423, (20,Years)), (2.449, (25,Years)), (2.46, (30,Years)),
#         #     #                      (2.445, (40,Years)), (2.42, (50,Years))]
#         #
#         #     usd_swap_3M_rates = [(1.35, 1), (1.526, 2),
#         #                          (1.678, 3), (1.8057, 4), (1.91, 5),
#         #                          (1.998, 6), (2.0758, 7), (2.138, 8), (2.1981, 9),
#         #                          (2.2515, 10), (2.295, 11), (2.335, 12),
#         #                          (2.368, 13), (2.395, 14), (2.416, 15),
#         #                          (2.49, 20), (2.501, 25), (2.509, 30),
#         #                          (2.512, 40), (2.492, 50)]
#         #
#         #     usd_ois.bootstrap_usd_ois_3M_curve(usd_3M_swap_rates=usd_swap_3M_rates,
#         #                                        discountCurve=ois_curve,
#         #                                        bootStrapMethod=BootStrapMethod.PiecewiseFlatForward)
#         #
#         #     # get the curve handle
#         #     # curve_handle = RelinkableYieldTermStructureHandle(usd_ois.usd_3M_c)
#         #
#         #     # Plot USD_3M libor curve curve
#         #     dates = None
#         #     forward_rate = None
#         #     try:
#         #         spot = usd_ois.usd_3M_c.referenceDate()
#         #         dates = [spot + Period(i, Months) for i in range(0, 60 * 12 + 3)]
#         #         # Zero rate
#         #         # print(usd_ois.usd_3M_c.zeroRate(Thirty360().yearFraction(spot, dates[1]), Compounded, Semiannual))
#         #         forward_rate = [usd_ois.usd_3M_c.forwardRate(d, Euribor3M().maturityDate(d),
#         #                                                      Actual360(), Simple).rate() for d in dates]
#         #     except Exception as e:
#         #         print(str(e))
#         #         pass
#         #     return usd_ois.usd_3M_c, forward_rate, dates


def construct_OIS_curve(usd_ois_quotes):
    '''
    :param usd_ois_quotes: a dict where the key is the tuple (start date, end date) and the value is the quote
    :return: a curve object
    '''
    # TODO: implement
    # create the OIS curve
    us_calendar = UnitedStates()
    valuation_date = [key for key in usd_ois_quotes][0][0]
    usd_ois = USDOIS(fixed_bond.pydate_to_qldate(valuation_date),
                     us_calendar)  # Pass in the Trade date- not the settle_date
    ois_rates = usd_ois_quotes
    usd_ois.create_ois_swaps(ois_rates)
    return usd_ois


def get_rate(ois_curve, start_date, end_date, **kwargs):
    '''
    :param curve:
    :param start_date:
    :param end_date:
    :param kwargs
    :return: a double: value of the rate implied by the curve between the two dates
    '''
    # c = ois_curve.ois_curve_c
    return ois_curve.ois_curve_c.forwardRate(fixed_bond.pydate_to_qldate(start_date),
                         fixed_bond.pydate_to_qldate(end_date),
                         Actual360(), Simple).rate()*100

def discounting_factor(ois_curve, end_date):
    '''
    Returns the discounting factor from the second date onto the first
    :param curve:
    :param start_date:
    :param end_date:
    :return: discounting factor
    '''
    return np.exp(-get_rate(ois_curve, ois_curve.valuationDate, end_date) *
                            ois_curve.calendar.businessDaysBetween(ois_curve.valuationDate,
                                                                   fixed_bond.pydate_to_qldate(end_date)) / 360)


def curve_from_disc_factors(disc_factors, calendar = UnitedStates()):
    '''
    Constructs a discounting curve from a list of discount factors
    :param disc_factors: list of tuples (disc_factor, start_date, end_date)
    :param kwargs: Extra stuff like daycount conventions etc
    :return:
    '''
    rates_dict = dict()
    for disc_factor,start_date, end_date in disc_factors:
        dt = calendar.businessDaysBetween(fixed_bond.pydate_to_qldate(start_date),
                                          fixed_bond.pydate_to_qldate(end_date)) / 360
        rates_dict[(start_date, end_date)] = -(1 / dt) * np.log(disc_factor)
    # [(lambda df, sd, ed : (rates_dict[(sd, ed)] = -(1/calendar.businessDaysBetween(sd,fixed_bond.pydate_to_qldate(ed)) / 360)*np.log(df)) for disc_factor,start_date, end_date in disc_factors]

    return construct_OIS_curve(rates_dict)

if __name__ == "__main__":
    spot_date = dt.date(2017, 9, 19)
    maturity_dates = [spot_date + dt.timedelta(days=30 * i) for i in range(1, 4)]
    ois_rates = [1.1450, 1.1490, 1.160]
    rate_dict = {}
    for md, rate in zip(maturity_dates, ois_rates):
        rate_dict[(spot_date, md)] = rate

    curve = construct_OIS_curve(rate_dict)
    r = get_rate(curve,spot_date,maturity_dates[0])
    print(r)