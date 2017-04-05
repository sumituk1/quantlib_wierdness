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
from datetime import datetime
from mosaicsmartdata.common.schedule import CSchedule
import numpy as np


def bond_convexity(price, par, T, coup, sd, dcf, freq,
                   calculateStub, ncd, dy=0.0001):
    ytm = bond_ytm.bond_ytm(price, par, T, coup, sd, dcf, freq, calculateStub, ncd)

    ytm_minus = ytm - dy
    price_minus = bond_price.bond_price(par, T, ytm_minus, coup, sd, dcf, freq, calculateStub, ncd)

    ytm_plus = ytm + dy
    price_plus = bond_price.bond_price(par, T, ytm_plus, coup, sd, dcf, freq, calculateStub, ncd)

    convexity = (price_minus + price_plus - 2 * price) / (price * (dy * dy)) / 100

    return convexity


def govbond_convx(price, sDate, nextCouponDate,
                  maturity, coupon,
                  frequency, daycount):
    sch = CSchedule()
    sd = datetime.strptime(sDate, '%Y-%m-%d')
    ed = datetime.strptime(maturity, '%Y-%m-%d')
    ncd = datetime.strptime(nextCouponDate, '%Y-%m-%d')
    calculate_stub = False

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    dc = DayCountConv.convertDayCountStr(daycount)

    T = sch.days_between_actual(ncd, ed) / 365
    dcf = sch.days_factor_2(ncd, ed, dc, freq)

    if sd != ncd:
        calculate_stub = True

    convexity = bond_convexity(price, 100, T, coupon, sd, dcf, freq, calculate_stub, ncd)

    return convexity


if __name__ == "__main__":
    # ==== input ==============================================================================================

    # 1. DE 15y benchmark
    price = 179.182
    sDate = "2016-08-08"  # settle date
    maturity = "2031-01-04"
    coupon = 5.5
    frequency = "A"
    nextCouponDate = "2017-01-04"  # next coupon date (This is needed especially when there is a big short stub
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
