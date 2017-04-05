"""
README
======
This file contains Python codes.
======
"""

""" Get yield-to-maturity of a bond """
import datetime as dt

import scipy.optimize as optimize
from risk import schedule
from common.constants import *
from pricing.Quantlib.bond import fixed_bond as bond
from risk.bond_mod_duration import *


# noinspection PyTypeChecker,PyShadowingNames
def bond_ytm(price, par, T, coup, sDate, dcf, freq, calculateStub=False,
             nextCouponDate=None, guess=0.05):
    # freq = float(freq)
    periods = T/dcf # <- excluding short stub
    coupon = coup/100.*par
    stub = 0
    dcf_stub = 1.0

    # calculate the front stub if passed in
    if calculateStub:
        dcf_stub = (nextCouponDate - sDate).days/365. # TODO: make this configurable as per ACT/ACT, ACT/360 etc.

    dt = [(i+1)*dcf for i in range(round(periods))]
    # ytm_func = lambda y: sum([coupon / (1 + y / freq) ** (freq * t) for t in dt]) \
    #                      + par / (1 + y / freq) ** (freq * T) - price

    ytm_func = lambda y: dcf_stub * coupon / (1 + dcf_stub * y) ** 1 +\
                         sum([dcf * coupon / (1 + dcf*y) ** ((t + dcf_stub)/dcf) for t in dt]) +\
                         par / (1 + dcf*y) ** ((T + dcf_stub)/dcf) - price

    return optimize.newton(ytm_func, guess)


# noinspection SpellCheckingInspection
def govbondytm(price,sd,nextCouponDate,ed,coupon,frequency,daycount):
    sch = schedule.CSchedule()
    # sd = datetime.strptime(sDate, '%Y-%m-%d')
    # ed = datetime.strptime(maturity, '%Y-%m-%d')
    # nextCouponDate = datetime.strptime(nextCouponDate, '%Y-%m-%d')

    if isinstance(nextCouponDate,dt.date):
        nextCouponDate = dt.datetime.combine(nextCouponDate, dt.datetime.min.time())

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)
    # convert daycount
    dc = DayCountConv.convertDayCountStr(daycount)
    T = sch.days_between_actual(nextCouponDate, ed) / 365
    dcf = sch.days_factor_2(nextCouponDate, ed, dc, freq)
    if sd != nextCouponDate:
        calculateStub = True
    ytm = bond_ytm(price, 100, T, coupon, sd, dcf, freq, calculateStub, nextCouponDate)

    return ytm

if __name__ == "__main__":
    # ytm = bond_ytm(95.0428, 100, 1.5, 5.75, 2)

    TOLERANCE = 15e-3

    # =============================== input ===================================================================
    # 1. Creating a Fixed Coupon Bond Corp.....
    issueDate = dt.datetime(2014,7,25) # -> python datetime
    maturityDate = dt.datetime(2020,7,27) # -> python datetime
    frequency = Frequency.SEMI # -> Coupon Frequency
    holidayCities = HolidayCities.EUR # -> Set the calendar
    daycount = DayCountConv.ACT_ACT # -> Set the dayCount
    # businessConvention = ql.Unadjusted
    dateGeneration = ql.DateGeneration.Backward
    # monthEnd = False
    coupon = 0.7
    price = 101.962
    settleDate = dt.datetime(2017, 2, 10)
    nextCouponDate = bond.getNextCouponDate(issueDate,maturityDate,frequency,holidayCities,settleDate) # next coupon date (This is needed especially when there is a big short stub
    print("next coupon date =%s"%nextCouponDate)
    ytm_corp = govbondytm(price, settleDate, nextCouponDate, maturityDate, coupon, frequency, daycount)
    print("YTM of corp=%s" % ytm_corp)

    # 2. Calculate PVBP for the Bond
    print("duration=%s"%govbondpvbp(price, settleDate, nextCouponDate, maturityDate, coupon, frequency, daycount,dy=0.01))

