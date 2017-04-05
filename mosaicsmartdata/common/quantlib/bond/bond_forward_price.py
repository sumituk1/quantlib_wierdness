"""
README
======
http://94.101.144.194/MagellanDemoStatic/tp/c10027/cc_0_82_0_0_8_10027_u10153_31_2.htm
======
"""
'''Non Quantlib implementation'''

""" Calculate forward price of a bond """
from mosaicsmartdata.common.quantlib.bond import bond_ytm
from mosaicsmartdata.common.quantlib.bond import bond_mod_duration
from mosaicsmartdata.common.quantlib.bond import bond_price
from mosaicsmartdata.common.constants import DayCountConv, CalendarFactory, Frequency
from datetime import datetime
from mosaicsmartdata.common.schedule import CSchedule
import scipy.optimize as optimize
import numpy as np


# calculate accrued interest
def bond_accrued(coup, start_date, end_date):
    sch = CSchedule()
    accrued_int = coup * sch.days_between_actual(start_date, end_date) / 365.25
    return accrued_int


# solve for clean_price from forward_price
def cleanprice_from_forward(forward_price, par, coup, spot_settle_date, forward_date, freq,
                            repo, prev_coupon_date, next_coupon_date, guess=100):
    sch = CSchedule()
    coupon = coup / 100 * par
    accrued_fwd = 0
    accrued_t0 = bond_accrued(coupon, prev_coupon_date, spot_settle_date)

    # day fraction between spot_settle and forward date
    dcf_fwd = sch.days_factor_2(spot_settle_date, forward_date, DayCountConv.ACT_360, freq)

    # day fraction between spot_settle and next coupon date
    next_coupon_dcf = sch.days_factor_2(spot_settle_date, next_coupon_date, DayCountConv.ACT_360, freq)

    # check if there's a coupon cashflow occurring between settle_date and forward_date
    # accrued_fwd = bond_accrued(coupon, prev_coupon_date, forward_date)

    if next_coupon_date < forward_date:
        # coupon between spot_settle and forward_date. forward_accrued needs to be calculated
        # w.r.t the next_coupon_date
        accrued_fwd = bond_accrued(coupon, next_coupon_date, forward_date)

        clean_price_fn = lambda spot_clean_price: forward_price - (
            (spot_clean_price + accrued_t0 - coupon / (1 + repo / 100 * next_coupon_dcf)) *
            (1 + repo / 100 * dcf_fwd))
    else:
        # No coupon between spot_settle and forward_date. forward_accrued needs to be calculated
        # w.r.t the prev_coupon_date and the forward_date
        accrued_fwd = bond_accrued(coupon, prev_coupon_date, forward_date)
        clean_price_fn = lambda spot_clean_price: forward_price - (
            (spot_clean_price + accrued_t0) * (1 + repo / 100 * dcf_fwd) - accrued_fwd)

    return optimize.newton(clean_price_fn, guess)


# calculate forward price from spot clean price
def bond_forward_price(price, par, coup, spot_settle_date, forward_date, freq,
                       repo, prev_coupon_date, next_coupon_date):
    sch = CSchedule()
    coupon = coup / 100 * par
    accrued_fwd = 0
    accrued_t0 = bond_accrued(coupon, prev_coupon_date, spot_settle_date)

    # day fraction between spot_settle and forward date
    dcf_fwd = sch.days_factor_2(spot_settle_date, forward_date, DayCountConv.ACT_360, freq)

    # day fraction between spot_settle and next coupon date
    next_coupon_dcf = sch.days_factor_2(spot_settle_date, next_coupon_date, DayCountConv.ACT_360, freq)

    # check if there's a coupon cashflow occurring between settle_date and forward_date
    # accrued_fwd = bond_accrued(coupon, prev_coupon_date, forward_date)

    if next_coupon_date < forward_date:
        # coupon between spot_settle and forward_date. forward_accrued needs to be calculated
        # w.r.t the next_coupon_date
        accrued_fwd = bond_accrued(coupon, next_coupon_date, forward_date)
        fwd_price = (price + accrued_t0 - coupon / (1 + repo / 100 * next_coupon_dcf)) * \
                    (1 + repo / 100 * dcf_fwd)  # - accrued_fwd - no need to subtract fwd_accrued
    else:
        # No coupon between spot_settle and forward_date. forward_accrued needs to be calculated
        # w.r.t the prev_coupon_date and the forward_date
        accrued_fwd = bond_accrued(coupon, prev_coupon_date, forward_date)
        fwd_price = (price + accrued_t0) * (1 + repo / 100 * dcf_fwd) - accrued_fwd

    return fwd_price


def govbond_forwardprice(price, spot_settle_date,
                         prev_coupon_date, next_coupon_date,
                         forward_date, coupon, frequency, repo):
    # sch = CSchedule()
    prev_coupon_date = datetime.strptime(prev_coupon_date, '%Y-%m-%d')
    spot_settle_date = datetime.strptime(spot_settle_date, '%Y-%m-%d')
    next_coupon_date = datetime.strptime(next_coupon_date, '%Y-%m-%d')
    forward_date = datetime.strptime(forward_date, '%Y-%m-%d')
    # maturity = datetime.strptime(maturity, '%Y-%m-%d')

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    # dc = DayCountConv.convertDayCountStr(daycount)

    forward_price = bond_forward_price(price, 100, coupon, spot_settle_date,
                                       forward_date, freq,
                                       repo, prev_coupon_date,
                                       next_coupon_date)

    return forward_price


def govbond_cleanprice_from_forwardprice(forward_price, spot_settle_date,
                                         prev_coupon_date, next_coupon_date,
                                         forward_date, coupon,
                                         frequency, repo):
    # sch = CSchedule()
    prev_coupon_date = datetime.strptime(prev_coupon_date, '%Y-%m-%d')
    spot_settle_date = datetime.strptime(spot_settle_date, '%Y-%m-%d')
    next_coupon_date = datetime.strptime(next_coupon_date, '%Y-%m-%d')
    forward_date = datetime.strptime(forward_date, '%Y-%m-%d')
    # maturity = datetime.strptime(maturity, '%Y-%m-%d')

    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    # dc = DayCountConv.convertDayCountStr(daycount)

    spot_clean_price = cleanprice_from_forward(forward_price, 100, coupon,
                                               spot_settle_date, forward_date,
                                               freq,repo, prev_coupon_date,
                                               next_coupon_date)

    return spot_clean_price


if __name__ == "__main__":
    # ==== input ==============================================================================================

    # 1. calculate T+6 DE 15y benchmark forward price

    price = 178.255000  # spot settle clean price
    spot_settle_date = "2016-08-10"  # settle date
    coupon = 5.5  # bond coupon
    frequency = "A"  # coupon frequency
    next_coupon_date = "2017-01-04"  # next coupon date
    prev_coupon_date = "2016-01-04"  # previous coupon date
    forward_date = "2016-08-17"  # forward settle date
    daycount = "ACT/ACT"  # daycount convention
    repo = -0.298  # repo rate in %

    print("forward price = ", govbond_forwardprice(price, spot_settle_date, prev_coupon_date, next_coupon_date,
                                                   forward_date, coupon, frequency, repo))

    # ==================================================================================================
    # 2. calculate spot clean_price from forward_price for DE 15y benchmark
    forward_price = 178.139289
    spot_settle_date = "2016-08-10"  # settle date
    coupon = 5.5  # bond coupon
    frequency = "A"  # coupon frequency
    next_coupon_date = "2017-01-04"  # next coupon date
    prev_coupon_date = "2016-01-04"  # previous coupon date
    forward_date = "2016-08-17"  # forward settle date
    daycount = "ACT/ACT"  # daycount convention
    repo = -0.298  # repo rate in %

    print("spot clean price = ",
          govbond_cleanprice_from_forwardprice(forward_price, spot_settle_date, prev_coupon_date, next_coupon_date,
                                               forward_date, coupon, frequency, repo))

    # price = 105.51562500
    # sDate = "2016-08-08"
    # maturity = "2046-05-15"
    # coupon = 2.5
    # frequency = "S"
    # daycount = "ACT/ACT"
    # nextCouponDate = "2017-11-15"

    # ==========================================================================================================
