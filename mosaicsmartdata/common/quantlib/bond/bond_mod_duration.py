""""
README
======
This file contains Python codes.
======
"""

""" Calculate modified duration of a bond """
from mosaicsmartdata.common.quantlib.bond.bond_ytm import bond_ytm
from mosaicsmartdata.common.quantlib.bond.bond_price import bond_price
from mosaicsmartdata.common.constants import DayCountConv, CalendarFactory, Frequency
import datetime as dt
from mosaicsmartdata.common.quantlib.bond import fixed_bond
from mosaicsmartdata.common.schedule import CSchedule


def bond_mod_duration(price, par, T, coup, sd, dcf, freq,
                      calculateStub, ncd, dy=0.0001):
    # calibrate a flat ytm based on close price

    ytm = bond_ytm(price, par, T, coup, sd, dcf, freq, calculateStub, ncd)

    # print(ytm)
    ytm_minus = ytm - dy
    price_minus = bond_price(par, T, ytm_minus, coup, sd, dcf, freq, calculateStub, ncd)

    ytm_plus = ytm + dy
    price_plus = bond_price(par, T, ytm_plus, coup, sd, dcf, freq, calculateStub, ncd)
    # bond_price(par, T, y, coup, sDate, dcf, freq=2, calculateStub=False, nextCouponDate=None):

    mod_duration = (price_minus - price_plus) / (2. * price * dy)
    return mod_duration


def govbond_pvbp(price,
                 settle_date,
                 maturity_date,
                 coupon,
                 frequency,
                 daycount,
                 holidayCities,
                 issue_date=None,
                 next_coupon_date=None,
                 dy=0.0001):
    sch = CSchedule()
    # sd = datetime.strptime(sDate, '%Y-%m-%d')
    # ed = datetime.strptime(maturity, '%Y-%m-%d')
    # ncd = datetime.strptime(nextCouponDate, '%Y-%m-%d')
    calculate_stub = False
    # convert frequency
    freq = Frequency.convertFrequencyStr(frequency)

    # convert daycount
    dc = DayCountConv.convertDayCountStr(daycount)

    # check next_coupon_date or issue_date
    if next_coupon_date is None:
        next_coupon_date = fixed_bond.getNextCouponDate(issueDate=issue_date,
                                                        maturityDate=maturity_date,
                                                        frequency=frequency,
                                                        holidayCities=holidayCities,
                                                        settleDate=settle_date)

        # TODO: Migrate this to quantlib later
        next_coupon_date = dt.datetime.combine(next_coupon_date, dt.datetime.min.time())
    else:
        if isinstance(next_coupon_date, dt.date):
            next_coupon_date = dt.datetime.combine(next_coupon_date, dt.datetime.min.time())

    T = sch.days_between_actual(next_coupon_date, maturity_date) / 365
    dcf = sch.days_factor_2(next_coupon_date, maturity_date, dc, freq)

    if settle_date != next_coupon_date:
        calculate_stub = True

    duration = bond_mod_duration(price, 100, T, coupon, settle_date, dcf, freq,
                                 calculate_stub, next_coupon_date, dy)

    return duration


if __name__ == "__main__":
    """
    Input parameters
    """
    # ==== input ==============================================================================================
    price = 178.536
    sDate = dt.datetime(2016, 8, 8)
    nextCouponDate = dt.datetime(2017, 1,
                                 4)  # next coupon date (This is needed especially when there is a big short stub
    maturity = dt.datetime(2031, 1, 4)
    coupon = 5.5
    holidayCities = "NY"
    frequency = "A"
    daycount = "ACT/ACT"

    # ==========================================================================================================

    # calculate duration based on close price
    print(govbond_pvbp(price=price,
                       settle_date=sDate,
                       next_coupon_date=nextCouponDate,
                       maturity_date=maturity,
                       coupon=coupon,
                       holidayCities=holidayCities,
                       frequency=frequency,
                       daycount=daycount))
