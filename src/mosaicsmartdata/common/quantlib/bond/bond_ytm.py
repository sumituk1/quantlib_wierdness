"""
README
======
This file contains Python codes.
======
"""

""" Get yield-to-maturity of a bond """
import datetime as dt
import QuantLib as ql
import scipy.optimize as optimize
from mosaicsmartdata.common import schedule
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.quantlib.bond import fixed_bond as bond
from mosaicsmartdata.common.quantlib.bond.bond_price import *
# from mosaicsmartdata.common.quantlib.bond.bond_mod_duration import govbond_pvbp


def bond_ytm(price, par, yrs_maturity, coupon, settle_date, dcf, freq, calculateStub=False,
             nextCouponDate=None, guess=0.05):
    # freq = float(freq)
    periods = yrs_maturity / dcf  # <- excluding short stub
    coupon = coupon / 100. * par
    stub = 0
    dcf_stub = 1.0

    # calculate the front stub if passed in
    if calculateStub:
        dcf_stub = (
                   nextCouponDate - settle_date).days / 365.  # TODO: make this configurable as per ACT/ACT, ACT/360 etc.

    dt = [(i + 1) * dcf for i in range(round(periods))]
    # ytm_func = lambda y: sum([coupon / (1 + y / freq) ** (freq * t) for t in dt]) \
    #                      + par / (1 + y / freq) ** (freq * T) - price

    ytm_func = lambda y: dcf_stub * coupon / (1 + dcf_stub * y) ** 1 + \
                         sum([dcf * coupon / (1 + dcf * y) ** ((t + dcf_stub) / dcf) for t in dt]) + \
                         par / (1 + dcf * y) ** ((yrs_maturity + dcf_stub) / dcf) - price

    return optimize.newton(ytm_func, guess)


def govbond_ytm(price, settle_date, next_coupon_date, maturity_date, coupon, frequency, day_count):
    sch = schedule.CSchedule()
    calculateStub=False
    # sd = datetime.strptime(sDate, '%Y-%m-%d')
    # ed = datetime.strptime(maturity, '%Y-%m-%d')
    # nextCouponDate = datetime.strptime(nextCouponDate, '%Y-%m-%d')

    if isinstance(next_coupon_date, dt.date):
        next_coupon_date = dt.datetime.combine(next_coupon_date, dt.datetime.min.time())

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)
    # convert daycount
    day_count = DayCountConv.convertDayCountStr(day_count)
    yrs_maturity = sch.days_between_actual(next_coupon_date, maturity_date) / 365
    dcf = sch.days_factor_2(next_coupon_date, maturity_date, day_count, freq)
    if settle_date != next_coupon_date:
        calculateStub = True
    ytm = bond_ytm(price=price,
                   par=100,
                   yrs_maturity=yrs_maturity,
                   coupon=coupon,
                   settle_date=settle_date,
                   dcf= dcf,
                   freq=freq,
                   calculateStub=calculateStub,
                   nextCouponDate=next_coupon_date)

    return ytm


if __name__ == "__main__":
    # ytm = bond_ytm(95.0428, 100, 1.5, 5.75, 2)

    TOLERANCE = 15e-3

    # =============================== input ===================================================================
    # 1. Creating a Fixed Coupon Bond Corp.....
    issueDate = dt.datetime(2017, 2, 15)  # -> python datetime
    maturityDate = dt.datetime(2047, 2, 15)  # -> python datetime
    frequency = Frequency.SEMI  # -> Coupon Frequency
    holidayCities = HolidayCities.USD  # -> Set the calendar
    daycount = DayCountConv.ACT_ACT  # -> Set the dayCount
    # businessConvention = ql.Unadjusted
    dateGeneration = ql.DateGeneration.Backward
    # monthEnd = False
    coupon = 3
    price = 103.8516
    settleDate = dt.datetime(2017, 8, 15)

    # next coupon date (This is needed especially when there is a big short stub)
    nextCouponDate = bond.getNextCouponDate(issue_date=issueDate,
                                            maturity_date=maturityDate,
                                            frequency=frequency,
                                            holidayCities=holidayCities,
                                            settle_date=settleDate)

    print("next coupon date =%s" % nextCouponDate)
    ytm_corp = govbond_ytm(price=price,
                           settle_date=settleDate,
                           next_coupon_date=nextCouponDate,
                           maturity_date=maturityDate,
                           coupon=coupon,
                           frequency=frequency,
                           day_count=daycount)
    print("YTM of corp=%s" % ytm_corp)

    # 2. Calculate PVBP for the Bond
    # print("duration=%s" % govbond_pvbp(price=price,
    #                                    settle_date=settleDate,
    #                                    next_coupon_date=nextCouponDate,
    #                                    maturity_date=maturityDate,
    #                                    coupon=coupon,
    #                                    day_count=daycount,
    #                                    frequency=frequency,
    #                                    dy=0.01))
