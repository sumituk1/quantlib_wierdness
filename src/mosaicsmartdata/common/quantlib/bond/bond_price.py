"""
README
======
This file contains Python codes.
======
"""
from mosaicsmartdata.common.schedule import CSchedule
import datetime as dt
from mosaicsmartdata.common.constants import DayCountConv, CalendarFactory, Frequency

""" Get bond price from YTM """


def bond_price(par,
               yrs_maturity,
               ytm,
               coupon,
               settle_date,
               dcf,
               calculateStub=False,
               next_coupon_date=None):
    # freq = float(freq)
    periods = yrs_maturity / dcf
    coupon = coupon / 100. * par
    stub = 0
    dcf_stub = 1.0

    # calculate the front stub if passed in
    if calculateStub:
        dcf_stub = (next_coupon_date - settle_date).days / 365.  # TODO: make this configurable as per ACT/ACT, ACT/360 etc.

    dt = [(i + 1) * dcf for i in range(round(periods))]

    price = dcf_stub * coupon / (1 + dcf_stub * ytm) ** 1 + \
            sum([dcf * coupon / (1 + dcf * ytm) ** ((t + dcf_stub) / dcf) for t in dt]) + \
            par / (1 + dcf * ytm) ** ((yrs_maturity + dcf_stub) / dcf)

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
                       calculateStub=calculate_stub,
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
