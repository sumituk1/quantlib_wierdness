from QuantLib import *
import datetime as dt
import numpy as np
from mosaicsmartdata.common.constants import BootStrapMethod
from mosaicsmartdata.common.quantlib.bond import fixed_bond
from mosaicsmartdata.common.constants import HolidayCities


class USDOIS:
    # today = Date_todaysDate()

    def __init__(self, *args):
        self.ff_local = FedFunds()  # We need an instance of the FF class which doesn;t need a forecast curve
        self.calendar = UnitedStates()  # calendar class
        self.valuationDate = Date_todaysDate()
        self.ois_curve_c = None  ## Holds the bootstrapped OIS curve
        self.helpers = None
        self.source_data = None
        self.holiday_cities = HolidayCities.USD

        if len(args) == 0:
            self.valuationDate = Date_todaysDate()
            Settings.instance().evaluationDate = Date_todaysDate()
        else:
            self.valuationDate = args[0]
            Settings.instance().evaluationDate = self.valuationDate
            calendar = args[1]
            self.holiday_cities = args[2]
            # self.usd_libor = USDLibor()

    # @property
    # def source_data(self):
    #     return self.source_data

    def create_deposit_rates(self, depo_rates):
        '''Creates a deposit rate helpers from incoming rates
        Input:
        depo_rates: list of tuples comprising of (start_date, end_date, rate, label)
        '''
        # get ONTN
        depo_rates = [x[0:-1] for x in depo_rates if x[-1] in ["ONTN", "TN","DUMMY"]]
        if len(depo_rates) > 0:
            self.helpers = [DepositRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                                              Period(1, Days),
                                              fixed_bond.calculateBusDays(self.holiday_cities,
                                                                          self.valuationDate,
                                                                          fixed_bond.pydate_to_qldate(sd)),
                                              TARGET(), Following, False, Actual360())
                            for sd, ed, rate in depo_rates]

    # Finally, we add OIS quotes up to 30 years.
    def create_ois_swaps(self, ois_swap_rates, helpers=None):
        ''' Creates a OIS rate helper from incoming OIS rates
            Input:
            ois_swap_rates: list of tuples comprising of (start_date, end_date, rate, label)
        '''
        if self.helpers is None:
            self.helpers = [
                DatedOISRateHelper(start_date, end_date, QuoteHandle(SimpleQuote(rate / 100)), self.ff_local)
                for start_date, end_date, rate in [tuple((fixed_bond.pydate_to_qldate(sd),
                                                          fixed_bond.pydate_to_qldate(ed),
                                                          rate)) for sd, ed, rate, label
                                                   in ois_swap_rates if label not in ['ONTN', 'TN']]]
        else:
            self.helpers += [DatedOISRateHelper(start_date,
                                                end_date,
                                                QuoteHandle(SimpleQuote(rate / 100)), self.ff_local)
                             for start_date, end_date, rate in [tuple((fixed_bond.pydate_to_qldate(sd),
                                                                       fixed_bond.pydate_to_qldate(ed),
                                                                       rate)) for sd, ed, rate, label
                                                                in ois_swap_rates if label not in ['ONTN', 'TN']]]
        # for start_date, end_date, rate in ois_swap_rates]
        self.ois_curve_c = PiecewiseLogCubicDiscount(0, self.calendar, self.helpers, Actual365Fixed())
        self.ois_curve_c.enableExtrapolation()
        # return ois_curve_c

    # The curve is an instance of PiecewiseLogCubicDiscount (corresponding to the PiecewiseYield-
    # Curve<Discount,LogCubic> class in C++;
    def bootstrap_usd_ois_3M_curve(self,
                                   usd_3M_swap_rates,
                                   discountCurve,
                                   bootStrapMethod=BootStrapMethod.PiecewiseLogCubicDiscount):

        discount_curve = RelinkableYieldTermStructureHandle()
        discount_curve.linkTo(discountCurve)
        self.helpers += [SwapRateHelper(QuoteHandle(SimpleQuote(rate / 100)),
                                        Period(int(label[:-1]), Years),
                                        TARGET(),
                                        Semiannual,
                                        Unadjusted,
                                        Thirty360(Thirty360.BondBasis),
                                        Euribor3M(),
                                        QuoteHandle(),
                                        Period(0, Days),
                                        discount_curve)
                         for sd, ed, rate, label in usd_3M_swap_rates if label not in ['ONTN', 'TN']]
        # for rate, tenor in usd_3M_swap_rates]

        if bootStrapMethod == BootStrapMethod.PiecewiseLogCubicDiscount:
            self.usd_3M_c = PiecewiseLogCubicDiscount(0, TARGET(), self.helpers, Actual365Fixed())
        elif bootStrapMethod == BootStrapMethod.PiecewiseFlatForward:
            self.usd_3M_c = PiecewiseFlatForward(0, TARGET(), self.helpers, Actual365Fixed())

        # Also, we enable extrapolation beyond the maturity of the last helper; that is mostly
        # for convenience as we retrieve rates to plot the curve near its far end.
        self.usd_3M_c.enableExtrapolation()

        # This is a test function

        # def test_usd_3m_bootstrap():
        #     usd_ois = USDOIS(Date(15, 5, 2017))  # Pass in the Trade date- not the settle_date
        #
        #     ois_swap_rates = [(1.189, (1, Years)), (1.345, (2, Years)), (1.477, (3, Years)),
        #                       (1.5907, (4, Years)), (1.681, (5, Years)), (1.758, (6, Years)),
        #                       (1.8258, (7, Years)), (1.879, (8, Years)), (1.9301, (9, Years)),
        #                       (1.9765, (10, Years)), (2.007, (12, Years)), (2.034, (15, Years)),
        #                       (2.053, (20, Years)), (2.071, (25, Years)), (2.085, (30, Years))]
        #
        #     # create the OIS curve
        #     ois_curve = usd_ois.create_ois_swaps(ois_swap_rates)
        #
        #     # usd_swap_3M_rates = [(1.356, (12,Months)), (1.5312, (2,Years)), (1.6421, (3,Years)),
        #     #                      (1.7677, (4,Years)), (1.8727, (5,Years)), (1.9526, (6,Years)),
        #     #                      (2.0228, (7,Years)), (2.0719, (8,Years)), (2.128, (9,Years)),
        #     #                      (2.205, (10,Years)), (2.225, (11,Years)), (2.262, (12,Years)),
        #     #                      (2.297, (13,Years)), (2.322, (14,Years)), (2.346, (15,Years)),
        #     #                      (2.423, (20,Years)), (2.449, (25,Years)), (2.46, (30,Years)),
        #     #                      (2.445, (40,Years)), (2.42, (50,Years))]
        #
        #     usd_swap_3M_rates = [(1.35, 1), (1.526, 2),
        #                          (1.678, 3), (1.8057, 4), (1.91, 5),
        #                          (1.998, 6), (2.0758, 7), (2.138, 8), (2.1981, 9),
        #                          (2.2515, 10), (2.295, 11), (2.335, 12),
        #                          (2.368, 13), (2.395, 14), (2.416, 15),
        #                          (2.49, 20), (2.501, 25), (2.509, 30),
        #                          (2.512, 40), (2.492, 50)]
        #
        #     usd_ois.bootstrap_usd_ois_3M_curve(usd_3M_swap_rates=usd_swap_3M_rates,
        #                                        discountCurve=ois_curve,
        #                                        bootStrapMethod=BootStrapMethod.PiecewiseFlatForward)
        #
        #     # get the curve handle
        #     # curve_handle = RelinkableYieldTermStructureHandle(usd_ois.usd_3M_c)
        #
        #     # Plot USD_3M libor curve curve
        #     dates = None
        #     forward_rate = None
        #     try:
        #         spot = usd_ois.usd_3M_c.referenceDate()
        #         dates = [spot + Period(i, Months) for i in range(0, 60 * 12 + 3)]
        #         # Zero rate
        #         # print(usd_ois.usd_3M_c.zeroRate(Thirty360().yearFraction(spot, dates[1]), Compounded, Semiannual))
        #         forward_rate = [usd_ois.usd_3M_c.forwardRate(d, Euribor3M().maturityDate(d),
        #                                                      Actual360(), Simple).rate() for d in dates]
        #     except Exception as e:
        #         print(str(e))
        #         pass
        #     return usd_ois.usd_3M_c, forward_rate, dates
