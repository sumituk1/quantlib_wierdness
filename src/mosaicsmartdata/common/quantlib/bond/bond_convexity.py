"""
README
======
This file contains Python codes.
======
"""

""" Calculate convexity of a bond """
from mosaicsmartdata.common.quantlib.bond import bond_ytm
from mosaicsmartdata.common.quantlib.bond import bond_mod_duration
from mosaicsmartdata.common.quantlib.bond import bond_price
from mosaicsmartdata.common.constants import DayCountConv, CalendarFactory, Frequency
import datetime as dt
from mosaicsmartdata.common.schedule import CSchedule
import numpy as np


def bond_convexity(price,
                   maturity_date,
                   coupon,
                   settle_date,
                   day_count,
                   dcf,
                   freq,
                   calculateStub,
                   next_coupon_date,
                   dy=0.0001,
                   par=100):
    sch = CSchedule()
    ytm = bond_ytm.govbond_ytm(price=price,
                               maturity_date=maturity_date,
                               coupon=coupon,
                               settle_date=settle_date,
                               day_count=day_count,
                               frequency=freq,
                               next_coupon_date=next_coupon_date)

    ytm_minus = ytm - dy
    yrs_maturity = sch.days_between_actual(next_coupon_date, maturity_date) / 365
    price_minus = bond_price.bond_price(par=par,
                                        yrs_maturity=yrs_maturity,
                                        ytm=ytm_minus,
                                        dcf=dcf,
                                        coupon=coupon, settle_date=settle_date,
                                        next_coupon_date=next_coupon_date)

    ytm_plus = ytm + dy
    price_plus = bond_price.bond_price(par=par,
                                       yrs_maturity=yrs_maturity,
                                       ytm=ytm_plus,
                                       dcf=dcf,
                                       coupon=coupon,
                                       settle_date=settle_date,
                                       next_coupon_date=next_coupon_date)

    convexity = (price_minus + price_plus - 2 * price) / (price * (dy * dy)) / 100

    return convexity


def govbond_convx(price, settle_date, next_coupon_date,
                  maturity_date, coupon,
                  frequency, daycount):
    sch = CSchedule()
    calculate_stub = False

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    dc = DayCountConv.convertDayCountStr(daycount)

    T = sch.days_between_actual(next_coupon_date, maturity_date) / 365
    dcf = sch.days_factor_2(next_coupon_date, maturity_date, dc, freq)

    if settle_date != next_coupon_date:
        calculate_stub = True

    convexity = bond_convexity(price=price,
                               par= 100,
                               maturity_date=maturity_date,
                               coupon= coupon,
                               dcf=dcf,
                               settle_date= settle_date,
                               day_count= dcf,
                               freq= freq,
                               calculateStub= calculate_stub,
                               next_coupon_date=next_coupon_date)

    return convexity


if __name__ == "__main__":
    # ==== input ==============================================================================================

    # 1. DE 15y benchmark
    price = 179.182
    sDate = dt.datetime(2016,8,8)  # settle date
    maturity = dt.datetime(2031,1,4)
    coupon = 5.5
    frequency = "A"
    nextCouponDate = dt.datetime(2017,1,4)  # next coupon date (This is needed especially when there is a big short stub
    daycount = "ACT/ACT"

    # price = 105.51562500
    # sDate = "2016-08-08"
    # maturity = "2046-05-15"
    # coupon = 2.5
    # frequency = "S"
    # daycount = "ACT/ACT"
    # nextCouponDate = "2017-11-15"

    # ==========================================================================================================

    print(govbond_convx(price, sDate, nextCouponDate, maturity, coupon, frequency, daycount))
