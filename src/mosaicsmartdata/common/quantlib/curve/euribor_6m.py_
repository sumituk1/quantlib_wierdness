# ---- Based on the paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2219548 ------------------------------
# Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping but Were Afraid to Ask
#                           By
#               Ferdinando M. Ametrano,Marco Bianchetti
# --------------------------------------------------------------------------------------------------------------------
import math
# import utils
# utils.set_default_plot_size()
from QuantLib import *
import seaborn as sns
from common.constants import BootStrapMethod
import matplotlib.pyplot as plt
from pricing.Quantlib.bond import fixed_bond
from pricing.Quantlib.curve import eonia

class Euribor_6M:
    today = Date_todaysDate()
    Settings.instance().evaluationDate = today

    def __init__(self,*args):
        if len(args) == 0:
            self.valuatioDate = Date_todaysDate()
        else:
            self.valuatioDate = args[0]

        self.euribor6m = Euribor6M()
        # self.eonia_c = Eonia()

    # The first three instruments are three 1-day deposit that give
    # us discounting between today and the
    # day after spot.
    def createDepositRate(self):
        self.helpers = [DepositRateHelper(  QuoteHandle(SimpleQuote(0.312/100)),
                                            Period(6,Months), 3,
                                            TARGET(), Following, False, Actual360())]

    # Then, we have a series of OIS quotes for the first month. They are modeled by instances of the
    # OISRateHelper class with varying tenors. They also require an instance of the Eonia class, which
    # doesn’t need a forecast curve and can be shared between the helpers
    def createFraRate(self, fraRates):
        # euribor6m = Euribor6M()
        self.helpers += [ FraRateHelper(QuoteHandle(SimpleQuote(rate/100)),
                                        start, self.euribor6m)
                                        for rate, start in fraRates]

    # Finally, we add OIS quotes up to 30 years.
    def createSwaps(self,euribor6mSwapRates,discountCurve):
        discount_curve = RelinkableYieldTermStructureHandle()
        discount_curve.linkTo(discountCurve)

        self.helpers += [ SwapRateHelper(QuoteHandle(SimpleQuote(rate/100)),
                                        Period(tenor, Years), TARGET(),
                                        Annual, Unadjusted,
                                        Thirty360(Thirty360.BondBasis),
                                        self.euribor6m, QuoteHandle(), Period(0, Days),
                                        discount_curve)
                                        for rate, tenor in euribor6mSwapRates]

    # The curve is an instance of PiecewiseLogCubicDiscount (corresponding to the PiecewiseYield-
    # Curve<Discount,LogCubic> class in C++;
    def bootStrapEuribor6MCurve(self, bootStrapMethod = BootStrapMethod.PiecewiseFlatForward):

        if bootStrapMethod == BootStrapMethod.PiecewiseLogCubicDiscount:
            self.euribor6m_c = PiecewiseLogCubicDiscount(0, TARGET(), self.helpers, Actual365Fixed())
            # Also, we enable extrapolation beyond the maturity of the last helper; that is mostly
            # for convenience as we retrieve rates to plot the curve near its far end.
            self.euribor6m_c.enableExtrapolation()
        elif bootStrapMethod == BootStrapMethod.PiecewiseFlatForward:
            self.euribor6m_c = PiecewiseFlatForward(0, TARGET(), self.helpers, Actual365Fixed())
            # Also, we enable extrapolation beyond the maturity of the last helper; that is mostly
            # for convenience as we retrieve rates to plot the curve near its far end.
            self.euribor6m_c.enableExtrapolation()

    @staticmethod
    def test_euribor_6m_boostrap():
        # Create a EONIA discount curve
        eonia = OISCurve.test_eonia_bootstrap()

        # Now create a Euribor 6M curve
        euribor_6m = Euribor_6M()
        # deposits = [(0.03565, 0),
        #             (0.03858, (1, Weeks)),
        #             (0.03840, (2, Weeks)),
        #             (0.03922, (3, Weeks))
        #             ]
        euribor_6m.createDepositRate()

        fraRate = [(0.293, 1), (0.272, 2), (0.260, 3),
                   (0.256, 4), (0.252, 5), (0.248, 6),
                   (0.254, 7), (0.261, 8), (0.267, 9),
                   (0.279, 10), (0.291, 11), (0.303, 12),
                   (0.318, 13), (0.335, 14), (0.352, 15),
                   (0.371, 16), (0.389, 17), (0.409, 18)]

        euribor_6m.createFraRate(fraRate)

        swapRates = [(0.424, 3), (0.576, 4), (0.762, 5),
                     (0.954, 6), (1.135, 7), (1.303, 8),
                     (1.452, 9), (1.584, 10), (1.809, 12),
                     (2.037, 15), (2.187, 20), (2.234, 25),
                     (2.256, 30), (2.295, 35), (2.348, 40),
                     (2.421, 50), (2.463, 60)]

        euribor_6m.createSwaps(swapRates, eonia.eonia_c)

        euribor_6m.bootStrapEuribor6MCurve(BootStrapMethod.PiecewiseLogCubicDiscount)

        # Plot Euribor_6M curve curve
        spot = euribor_6m.euribor6m_c.referenceDate()
        dates = [spot + Period(i, Months) for i in range(0, 60 * 12 + 1)]
        rates = [euribor_6m.euribor6m_c.forwardRate(d, euribor_6m.euribor6m.maturityDate(d),
                                                    Actual360(), Simple).rate() for d in dates]
        return rates,dates

if __name__ == "__main__":
    rates, dates = Euribor_6M().test_euribor_6m_boostrap()
    fig, ax = plt.subplots()
    ax.plot_date([fixed_bond.qldate_to_pydate(d) for d in dates], [100*rate for rate in rates],'-')
    plt.show()

    # nodes = list(eonia_curve_ff.nodes())
    # print(nodes[:9])
