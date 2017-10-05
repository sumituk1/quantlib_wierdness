"""
README
======
This file contains Python codes.
======
"""
from mosaicsmartdata.common import schedule
import datetime as dt
from mosaicsmartdata.common.constants import DayCountConv, CalendarFactory, Frequency

""" Get bond price from YTM """
"""
Input
======
ytm : yield of the bond (Expects to be in % i.e. 3.25 should be passed in for 3.25%)
coupon : coupon of the bond (Expects to be in % i.e. 3.25 should be passed in for 3.25%)
settle_date : bond settlement date
maturity_date: maturity_date of the bond
day_count: DayCount convention like ACT/ACT or ACT/360
frequency: Coupon Frequency (should be of Enum type Frequency)
next_coupon_date: NCD of the bond since settlement
======
"""
def bond_price(ytm,
               coupon,
               settle_date,
               maturity_date,
               day_count,
               frequency,
               next_coupon_date=None,
               par=100):
    # freq = float(freq)
    sch = schedule.CSchedule()
    calculateStub = False
    coupon = coupon / 100. * par

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency, coupon)
    import datetime as dt
    if isinstance(next_coupon_date, dt.date):
        # convert daycount
        day_count = DayCountConv.convertDayCountStr(day_count)
        next_coupon_date = dt.datetime.combine(next_coupon_date, dt.datetime.min.time())
        dcf = sch.days_factor_2(next_coupon_date, maturity_date, day_count, freq)
        if settle_date != next_coupon_date:
            calculateStub = True
        if "360" in day_count.split("/")[-1]:
            yrs_maturity = sch.days_between_actual(next_coupon_date, maturity_date) / 360.
        else:
            yrs_maturity = sch.days_between_actual(next_coupon_date, maturity_date) / 365.
    else:
        ## either no next_coupon_date passed in or type is wrong
        if freq == Frequency.SEMI:
            dcf = 6 / 12
        elif freq == Frequency.QUARTERLY:
            dcf = 3 / 12
        elif freq == Frequency.MONTHLY:
            dcf = 1 / 12
        else:
            dcf = 1
        if "360" in day_count.split("/")[-1]:
            yrs_maturity = sch.days_between_actual(settle_date, maturity_date) / 360.
        else:
            yrs_maturity = sch.days_between_actual(settle_date, maturity_date) /365.

    periods = yrs_maturity / dcf

    # calculate the front stub if passed in
    if calculateStub:
        if "360" in day_count.split("/")[-1]:
            dcf_stub = (next_coupon_date - settle_date).days / 360.
        else:
            dcf_stub = (next_coupon_date - settle_date).days / 365.
    else:
        dcf_stub = 0

    dt = [(i + 1) * dcf for i in range(round(periods))]

    price = dcf_stub * coupon / (1 + dcf_stub * ytm/100) ** 1 + \
            sum([dcf * coupon / (1 + dcf * ytm/100) ** ((t + dcf_stub) / dcf) for t in dt]) + \
            par / (1 + dcf * ytm/100) ** ((yrs_maturity + dcf_stub) / dcf)

    return price


def govbond_price_from_yield(settle_date,
                             next_coupon_date,
                             maturity_date,
                             coupon,
                             frequency,
                             day_count,
                             ytm,
                             par=100):
    sch = CSchedule()
    calculate_stub = False

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    day_count = DayCountConv.convertDayCountStr(day_count)
    yrs_maturity = sch.days_between_actual(next_coupon_date, maturity_date) / 365
    dcf = sch.days_factor_2(next_coupon_date, maturity_date, day_count, freq)

    if settle_date != next_coupon_date:
        calculate_stub = True
    price = bond_price(par=par,
                       yrs_maturity=yrs_maturity,
                       ytm=ytm,
                       coupon=coupon,
                       settle_date=settle_date,
                       dcf=dcf,
                       next_coupon_date=next_coupon_date)
    return price


if __name__ == "__main__":
    """
    Input parameters
    """

    # ==== input ==============================================================================================
    price = 178.013
    settle_date = dt.datetime(2016,8,8)
    next_coupon_date = dt.datetime(2017,1,4)  # next coupon date (This is needed especially when there is a big short stub
    maturity_date = dt.datetime(2031,1,4)
    coupon = 5.5
    frequency = "A"
    day_count = "ACT/ACT"
    ytm = 0.00034
    # ==========================================================================================================

    print(govbond_price_from_yield(settle_date, next_coupon_date, maturity_date, coupon, frequency, day_count, ytm))
