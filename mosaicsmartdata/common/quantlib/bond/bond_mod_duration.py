""""
README
======
This file contains Python codes.
======
"""

""" Calculate modified duration of a bond """
import datetime as dt
from mosaicsmartdata.common.constants import DayCountConv, Frequency
from mosaicsmartdata.common.quantlib.bond.bond_price import bond_price
from mosaicsmartdata.common.quantlib.bond.bond_ytm import govbond_ytm
from mosaicsmartdata.common.schedule import CSchedule


def bond_mod_duration(price, par,yrs_maturity, maturity_date, coupon, settle_date, day_count, frequency,
                      calculateStub, next_coupon_date, dy=0.0001):
    # calibrate a flat ytm based on close price

    ytm = govbond_ytm(price=price, coupon=coupon, settle_date=settle_date, maturity_date=maturity_date,
                      day_count=day_count, frequency=frequency,next_coupon_date=next_coupon_date)

    # print(ytm)
    ytm_minus = ytm - dy
    price_minus = bond_price(par, yrs_maturity, ytm_minus, coupon, settle_date,
                             day_count, calculateStub, next_coupon_date)

    ytm_plus = ytm + dy
    price_plus = bond_price(par, yrs_maturity, ytm_plus, coupon, settle_date,
                            day_count, calculateStub, next_coupon_date)
    # bond_price(par, T, y, coup, sDate, dcf, freq=2, calculateStub=False, nextCouponDate=None):

    mod_duration = (price_minus - price_plus) / (2. * price * dy)
    return mod_duration


def govbond_pvbp(price,
                 settle_date,
                 maturity_date,
                 coupon,
                 day_count,
                 frequency,
                 next_coupon_date=None,
                 dy=0.0001):
    sch = CSchedule()
    calculate_stub = False
    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    dc = DayCountConv.convertDayCountStr(day_count)

    # check next_coupon_date or issue_date
    if next_coupon_date is None:
        raise ValueError("Next_coupon_date not passed in")
    else:
        if isinstance(next_coupon_date, dt.date):
            next_coupon_date = dt.datetime.combine(next_coupon_date, dt.datetime.min.time())

    yrs_maturity = sch.days_between_actual(next_coupon_date, maturity_date) / 365
    dcf = sch.days_factor_2(next_coupon_date, maturity_date, dc, freq)

    if settle_date != next_coupon_date:
        calculate_stub = True

    duration = bond_mod_duration(price=price, par=100, yrs_maturity= yrs_maturity,
                                 maturity_date=maturity_date,
                                 settle_date= settle_date,
                                 day_count=dcf, frequency=freq, calculateStub=calculate_stub,
                                 next_coupon_date= next_coupon_date, dy= dy, coupon=coupon)

    return duration


if __name__ == "__main__":
    """
    Input parameters
    """
    # ==== input ==============================================================================================
    price = 178.536
    settle_date = dt.datetime(2016, 8, 8)
    next_coupon_date = dt.datetime(2017, 1, 4)
    maturity = dt.datetime(2031, 1, 4)
    coupon = 5.5
    holidayCities = "NY"
    frequency = "A"
    daycount = "ACT/ACT"

    # ==========================================================================================================

    # calculate duration based on close price
    print(govbond_pvbp(price=price,
                       day_count=daycount,
                       settle_date=settle_date,
                       next_coupon_date=next_coupon_date,
                       maturity_date=maturity,
                       coupon=coupon,
                       frequency=frequency))
