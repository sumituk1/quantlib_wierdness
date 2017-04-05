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


def bond_price(par, T, y, coup, sDate, dcf,
               freq=2, calculateStub=False,
               nextCouponDate=None):
    # freq = float(freq)
    periods = T / dcf
    coupon = coup / 100. * par
    stub = 0
    dcf_stub = 1.0

    # calculate the front stub if passed in
    if calculateStub:
        dcf_stub = (nextCouponDate - sDate).days / 365.  # TODO: make this configurable as per ACT/ACT, ACT/360 etc.

    dt = [(i + 1) * dcf for i in range(round(periods))]

    price = dcf_stub * coupon / (1 + dcf_stub * y) ** 1 + \
            sum([dcf * coupon / (1 + dcf * y) ** ((t + dcf_stub) / dcf) for t in dt]) + \
            par / (1 + dcf * y) ** ((T + dcf_stub) / dcf)

    return price


def govbond_price_from_yield(sd, ncd, ed, coupon, frequency, daycount, ytm):
    sch = CSchedule()
    # sd = datetime.strptime(sDate, '%Y-%m-%d')
    # ed = datetime.strptime(maturity, '%Y-%m-%d')
    # ncd = datetime.strptime(nextCouponDate, '%Y-%m-%d')
    calculate_stub = False
    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)
    # convert daycount
    dc = DayCountConv.convertDayCountStr(daycount)
    T = sch.days_between_actual(ncd, ed) / 365
    dcf = sch.days_factor_2(ncd, ed, dc, freq)

    if sd != ncd:
        calculate_stub = True
    price = bond_price(100, T, ytm, coupon, sd, dcf, freq, calculate_stub, ncd)
    return price


if __name__ == "__main__":
    """
    Input parameters
    """

    # ==== input ==============================================================================================
    price = 178.013
    sDate = "2016-08-08"
    nextCouponDate = "2017-01-04"  # next coupon date (This is needed especially when there is a big short stub
    maturity = "2031-01-04"
    coupon = 5.5
    frequency = "A"
    daycount = "ACT/ACT"
    ytm = 0.00034
    # ==========================================================================================================

    print(govbond_price_from_yield(sDate, nextCouponDate, maturity, coupon, frequency, daycount, ytm))
