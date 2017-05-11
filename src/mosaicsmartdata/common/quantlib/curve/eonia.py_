# ---- Based on the paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2219548 ------------------------------
# Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping but Were Afraid to Ask
#                           By
#               Ferdinando M. Ametrano,Marco Bianchetti
# --------------------------------------------------------------------------------------------------------------------

import math
# import utils
# utils.set_default_plot_size()
from QuantLib import *
from common.constants import BootStrapMethod
import seaborn as sns
import matplotlib.pyplot as plt
from pricing.Quantlib.bond import fixed_bond

class OISCurve:
    today = Date_todaysDate()
    Settings.instance().evaluationDate = today
    eonia_local = Eonia()

    def __init__(self,*args):
        if len(args) == 0:
            self.valuatioDate = Date_todaysDate()
        else:
            self.valuatioDate = args[0]

        # self.eonia_c = Eonia()

    # The first three instruments are three 1-day deposit that give
    # us discounting between today and the
    # day after spot.
    def createDepositRate(self,depositRates):
        self.helpers = [ DepositRateHelper( QuoteHandle(SimpleQuote(rate/100)),
                                                Period(1,Days), fixingDays,
                                                TARGET(), Following, False, Actual360())
                                                for rate, fixingDays in depositRates]

    # Then, we have a series of OIS quotes for the first month. They are modeled by instances of the
    # OISRateHelper class with varying tenors. They also require an instance of the Eonia class, which
    # doesn’t need a forecast curve and can be shared between the helpers
    def createOneMonthOIS(self, monthlyRates):
        self.helpers += [ OISRateHelper(2, Period(*tenor), QuoteHandle(SimpleQuote(rate/100)), self.eonia_local)
                                        for rate, tenor in monthlyRates
                          ]

    # # OIS forwards on ECB dates
    def createOISForwardOnECBDates(self, ecbForwardRates):

        self.helpers += [ DatedOISRateHelper(start_date, end_date,QuoteHandle(SimpleQuote(rate/100)), self.eonia_local)
                            for rate, start_date, end_date in ecbForwardRates]

    # Finally, we add OIS quotes up to 30 years.
    def createOISSwaps(self,oisSwapRates):

        self.helpers += [OISRateHelper(2, Period(*tenor), QuoteHandle(SimpleQuote(rate / 100)), self.eonia_local)
                         for rate, tenor in oisSwapRates]

    # The curve is an instance of PiecewiseLogCubicDiscount (corresponding to the PiecewiseYield-
    # Curve<Discount,LogCubic> class in C++;
    def bootStrapOISCurve(self, bootStrapMethod = BootStrapMethod.PiecewiseFlatForward):

        if bootStrapMethod == BootStrapMethod.PiecewiseLogCubicDiscount:
            self.eonia_c = PiecewiseLogCubicDiscount(0, TARGET(), self.helpers, Actual365Fixed())
            # Also, we enable extrapolation beyond the maturity of the last helper; that is mostly
            # for convenience as we retrieve rates to plot the curve near its far end.
            self.eonia_c.enableExtrapolation()
        elif bootStrapMethod == BootStrapMethod.PiecewiseFlatForward:
            self.eonia_c = PiecewiseFlatForward(0, TARGET(), self.helpers, Actual365Fixed())
            # Also, we enable extrapolation beyond the maturity of the last helper; that is mostly
            # for convenience as we retrieve rates to plot the curve near its far end.
            self.eonia_c.enableExtrapolation()

    @staticmethod
    def test_eonia_bootstrap():
        eonia = OISCurve()

        deposits = [(0.04, 0),
                    (0.04, 1),
                    (0.04, 2)
                    ]
        eonia.createDepositRate(deposits)

        monthlyOISRates = [(0.070, (1, Weeks)),
                           (0.069, (2, Weeks)),
                           (0.078, (3, Weeks)),
                           (0.074, (1, Months))
                           ]

        eonia.createOneMonthOIS(monthlyOISRates)

        oisSwapRates = [(0.002, (15, Months)), (0.008, (18, Months)),
                        (0.021, (21, Months)), (0.036, (2, Years)),
                        (0.127, (3, Years)), (0.274, (4, Years)),
                        (0.456, (5, Years)), (0.647, (6, Years)),
                        (0.827, (7, Years)), (0.996, (8, Years)),
                        (1.147, (9, Years)), (1.280, (10, Years)),
                        (1.404, (11, Years)), (1.516, (12, Years)),
                        (1.764, (15, Years)), (1.939, (20, Years)),
                        (2.003, (25, Years)), (2.038, (30, Years))
                        ]

        eonia.createOISSwaps(oisSwapRates)

        eonia.bootStrapOISCurve(BootStrapMethod.PiecewiseLogCubicDiscount)
        return eonia

if __name__ == "__main__":

    eonia = OISCurve.test_eonia_bootstrap()

    # Plot EONIA curve upto 2 yrs
    today = eonia.valuatioDate
    end = today + Period(2,Years)
    dates = [ Date(serial) for serial in range(today.serialNumber(),end.serialNumber()+1)]
    rates_c = [ eonia.eonia_c.forwardRate(d, TARGET().advance(d,1,Days),Actual360(), Simple).rate()for d in dates]

    fig, ax = plt.subplots()
    ax.plot_date([fixed_bond.qldate_to_pydate(d) for d in dates], [100*rate for rate in rates_c],'-')
    # plt.show()

    # Turn-of-year jumps
    # eonia_curve_ff = PiecewiseFlatForward(0, TARGET(),helpers, Actual365Fixed())
    # eonia_curve_ff.enableExtrapolation()

    # Now look at the jumps...
    # fig, ax = plt.subplots()
    end = today + Period(6,Months)
    dates = [ Date(serial) for serial in range(today.serialNumber(),end.serialNumber()+1)]
    rates_ff = [ eonia.eonia_c.forwardRate(d, TARGET().advance(d,1,Days),
                                            Actual360(), Simple).rate()for d in dates]

    fig, ax = plt.subplots()
    ax.plot_date([fixed_bond.qldate_to_pydate(d) for d in dates], [100*rate for rate in rates_ff],'-')
    plt.show()

    # nodes = list(eonia_curve_ff.nodes())
    # print(nodes[:9])
