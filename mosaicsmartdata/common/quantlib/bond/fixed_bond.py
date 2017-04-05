# http://gouthamanbalaraman.com/blog/quantlib-bond-modeling.html
# Also - for calibrating NS curve: http://quant.stackexchange.com/questions/30604/
# how-to-construct-a-corporate-yield-curve
# NS curve fitting:- https://github.com/kirilldolmatov/QuantLib (http://quant.stackexchange.com/questions/28154
# /quantlib-fittedbonddiscountcurve-fitresults-error)
import QuantLib as ql
# import QuantLib.time.date as dt
from mosaicsmartdata.common.constants import *
import numpy as np
import datetime as dt
import locale
import six
from mosaicsmartdata.common.isda_daycounters import (actual360, actual365,
                                                     actualactual, thirty360)
import re

# from QuantLib.termstructures.yields.zero_curve import ZeroCurve

# todaysDate = ql.Date(15, 1, 2015)
# ql.Settings.instance().evaluationDate = todaysDate
# spotDates = [ql.Date(15, 1, 2015), ql.Date(15, 7, 2015), ql.Date(15, 1, 2016)]
# spotRates = [0.0, 0.005, 0.007]
dayCount = ql.Thirty360()
calendar = ql.UnitedStates
interpolation = ql.Linear()
compounding = ql.Compounded

_dayOfWeekName = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                  'Friday', 'Saturday', 'Sunday']
_monthName = ['January', 'February', 'March', 'April', 'May',
              'June', 'July', 'August', 'September', 'October',
              'November', 'December']
_shortMonthName = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                   'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

date_re_list = [  # Styles: (1)
    (re.compile('([0-9]+)-([A-Za-z]+)-([0-9]{2,4})'),
     (3, 2, 1)),
    # Styles: (2)
    (re.compile("([0-9]{4,4})([0-9]{2,2})([0-9]{2,2})"),
     (1, 2, 3)),
    # Styles: (3)
    (re.compile("([0-9]+)/([0-9]+)/([0-9]{2,4})"),
     (2, 1, 3)),
    # Styles: (4)
    (re.compile("([0-9](1,2))([A-Za-z](3,3))([0-9](2,4))"),
     (3, 2, 1)),
    # Styles: (5)
    (re.compile("([0-9]{2,4})-([0-9]+)-([0-9]+)"),
     (1, 2, 3))]

DAYS = 1
MONTHS = 2
YEARS = 3


def _partition_date(date):
    """
    Partition a date string into three sub-strings
    year, month, day
    The following styles are understood:
    (1) 22-AUG-1993 or
        22-Aug-03 (2000+yy if yy<50)
    (2) 20010131
    (3) mm/dd/yy or
        mm/dd/yyyy
    (4) 10Aug2004 or
        10Aug04
    (5) yyyy-mm-dd
    """

    date = str.lstrip(str.rstrip(date))
    for reg, idx in date_re_list:
        mo = reg.match(date)
        if mo != None:
            return (mo.group(idx[0]), mo.group(idx[1]),
                    mo.group(idx[2]))
    raise Exception("couldn't partition date: %s" % date)


def _parsedate(date):
    """
    Parse a date string and return the tuple
    (year, month, day)
    """
    (yy, mo, dd) = _partition_date(date)
    if len(yy) == 2:
        yy = locale.atoi(yy)
        yy += 2000 if yy < 50 else 1900
    else:
        yy = locale.atoi(yy)

    try:
        mm = locale.atoi(mo)
    except:
        mo = str.lower(mo)
        if not mo in _shortMonthName:
            raise Exception("Bad month name: " + mo)
        else:
            mm = _shortMonthName.index(mo) + 1

    dd = locale.atoi(dd)
    return (yy, mm, dd)


def pydate(date):
    """
    Accomodate date inputs as string or python date
    """

    if isinstance(date, dt.datetime):
        return date
    else:
        yy, mm, dd = _parsedate(date)
        return dt.datetime(yy, mm, dd)


def pydate_to_qldate(date):
    """
    Converts a datetime object or a date string
    into a QL Date.
    """

    if isinstance(date, ql.Date):
        return date
    if isinstance(date, six.string_types):
        yy, mm, dd = _parsedate(date)
        return ql.Date(dd, mm, yy)
    else:
        return ql.QuantLib.Date(date.day, date.month, date.year)


def qldate_to_pydate(date):
    """
    Converts a QL Date to a datetime
    """
    if isinstance(date, ql.Date):
        return dt.datetime(date.year(), date.month(), date.dayOfMonth()).date()
    else:
        return None


def df_to_zero_curve(rates, settlement_date, daycounter=ql.Actual365Fixed):
    """ Converts a pandas data frame into a QL zero curve. """

    dates = [pydate_to_qldate(dt) for dt in rates.index]
    dates.insert(0, pydate_to_qldate(settlement_date))

    # arbitrarily extend the curve a few years to provide flat
    # extrapolation
    dates.append(dates[-1] + 365 * 2)

    values = rates.values.tolist()
    values.insert(0, values[0])
    values.append(values[-1])

    return ql.ZeroCurve(dates, values, daycounter)


# Maps incoming holidayCities to quantlib Calendar
def mapHolidayCalendar(holidayCities):
    if holidayCities == HolidayCities.USA:
        return ql.UnitedStates()
    elif holidayCities == HolidayCities.EUR:
        return ql.Germany()
    elif holidayCities == HolidayCities.GBP:
        return ql.UnitedKingdom()
    elif holidayCities == HolidayCities.JPY:
        return ql.Japan()
    elif holidayCities == HolidayCities.TARGET:
        return ql.TARGET()
    elif holidayCities == HolidayCities.IT:
        return ql.Italy()
    elif holidayCities == HolidayCities.ISR:
        return ql.Israel()
    elif holidayCities == HolidayCities.CHINA:
        return ql.China()


# Maps incoming daycount to quantlib daycount
def mapDayCountConv(dayCount):
    if dayCount == DayCountConv.ACT_ACT:
        return ql.ActualActual()
    elif dayCount == DayCountConv.ACT_360:
        return ql.Actual360()
    elif dayCount == DayCountConv.ACT_365:
        return ql.Actual365Fixed()
    elif dayCount == DayCountConv.ACT_252:
        return ql.Business252()
    elif dayCount == DayCountConv.ThirtyE360:
        return ql.Thirty360(ql.Thirty360.EurobondBasis)
    elif dayCount == DayCountConv.Thirty360_US:
        return ql.Thirty360(ql.Thirty360.USA)
    elif dayCount == DayCountConv.Thirty360:
        return ql.Thirty360()
    elif dayCount == DayCountConv.BASIC30_360:
        return ql.BASIC30_360()


# map incoming frequency to QL frequency
def mapFrequency(freq):
    if freq == Frequency.ANNUAL:
        return ql.Annual
    elif freq == Frequency.DAILY:
        return ql.Daily
    elif freq == Frequency.MONTHLY:
        return ql.Monthly
    elif freq == Frequency.QUARTERLY:
        return ql.Quarterly
    elif freq == Frequency.SEMI:
        return ql.Semiannual


# Calculates the number of business days between 2 given dates
def calculateBusDays(holidayCities, py_sd, py_ed):
    ql_sd = pydate_to_qldate(py_sd)
    ql_ed = pydate_to_qldate(py_ed)
    if holidayCities == HolidayCities.USA:
        cd = ql.UnitedStates()
    elif holidayCities == HolidayCities.EUR:
        cd = ql.Germany()
    elif holidayCities == HolidayCities.GBP:
        cd = ql.UnitedKingdom()
    elif holidayCities == HolidayCities.JPY:
        cd = ql.Japan()
    return cd.businessDaysBetween(ql_sd, ql_ed)


# Calculates the number of business days between 2 given dates
def calculateYearFrac(dayCount, sd, ed):
    if isinstance(sd, ql.Date):
        # if quantlib date, then convert to python datetime
        sd = qldate_to_pydate(sd)
    if isinstance(sd, dt.datetime):
        # if python datetime, convert to python date
        sd = sd.date()

    if isinstance(ed, ql.Date):
        # if quantlib date, then convert to python datetime
        ed = qldate_to_pydate(ed)
    if isinstance(ed, dt.datetime):
        # if python datetime, convert to python date
        ed = ed.date()

    # TODO: Need to have a implementation for each of the dayCount
    if dayCount == DayCountConv.ACT_360:
        return actual360.year_fraction(start_date=sd, end_date=ed)
    elif (dayCount == DayCountConv.ACT_365) or (dayCount == DayCountConv.ACT_365L):
        return actual365.year_fraction(start_date=sd, end_date=ed)
    elif (dayCount == DayCountConv.Thirty360) \
            or (dayCount == DayCountConv.BASIC30_360) \
            or (dayCount == DayCountConv.NASD30_360) \
            or (dayCount == DayCountConv.Thirty360_US) \
            or (dayCount == DayCountConv.ThirtyE360):
        return thirty360.year_fraction(start_date=sd, end_date=ed)
    else:
        # all act/act
        return actualactual.year_fraction(start_date=sd, end_date=ed)


def calculateAccrued(dcf, coupon, freq, dayCount=ql.Thirty360, faceValue=100):
    # busDays = calculateBusDays(holidayCity, sd,ed)
    return (coupon / Frequency.getFrequencyNumber(
        freq)) * faceValue * dcf  # <-- dcf = (t2 - t1).days / (next_coupon - last_coupon).days
    # if freq == Frequency.ANNUAL:
    #     return coupon * faceValue * dcf
    # elif freq == Frequency.DAILY:
    #     return coupon * (1 / 365) * faceValue * dcf
    # elif freq == Frequency.MONTHLY:
    #     return coupon * (1 / 12) * faceValue * dcf
    # elif freq == Frequency.QUARTERLY:
    #     return coupon * (1 / 4) * faceValue * dcf
    # elif freq == Frequency.SEMI:
    #     return coupon * (1 / 2) * faceValue * dcf


# Creates a fixed Rate bond
def createFixedRateBond(issue_date, maturity_date, frequency, holidayCities,
                        coupon, inDayCount=DayCountConv.ACT_ACT,
                        faceValue=100, settlementDays=2):
    ql_calendar = mapHolidayCalendar(holidayCities)
    ql_dayCount = mapDayCountConv(inDayCount)
    ql_frequency = ql.Period(mapFrequency(frequency))
    business_convention = ql.Unadjusted
    date_generation = ql.DateGeneration.Backward
    month_end = False
    schedule = ql.Schedule(issue_date, maturity_date, ql_frequency, ql_calendar, business_convention,
                           business_convention, date_generation, month_end)

    fixedRateBond = ql.FixedRateBond(settlementDays, faceValue, schedule, [coupon], ql_dayCount)

    return fixedRateBond


def ytm_given_price(bond, targetClean, frequency):
    ytm = bond.bondYield(targetClean, ql.ActualActual(ql.ActualActual.Bond), ql.Compounded, ql.Annual)
    return ytm


# creates a Schedule for the cashflows.
def __createSchedule(py_issueDate, py_maturityDate, frequency, holidayCities):
    # Creating a Schedule
    py_issueDate = pydate_to_qldate(py_issueDate)
    py_maturityDate = pydate_to_qldate(py_maturityDate)
    tenor = ql.Period(mapFrequency(frequency))
    calendar = mapHolidayCalendar(holidayCities)
    businessConvention = ql.Unadjusted
    dateGeneration = ql.DateGeneration.Backward
    monthEnd = False
    schedule = ql.Schedule(py_issueDate, py_maturityDate, tenor, calendar, businessConvention,
                           businessConvention, dateGeneration, monthEnd)
    return schedule


# Returns the days elapsed since last Coupon date
def busDaysSinceLastCoupon(issueDate, maturityDate, frequency, holidayCities, currDate):
    # first create a Sceduke of cashflows
    schedule = __createSchedule(pydate_to_qldate(issueDate), pydate_to_qldate(maturityDate),
                                frequency, holidayCities)
    prevCouponDate = [i for i in list(schedule) if i < pydate_to_qldate(currDate)][-1]

    return calculateBusDays(holidayCities, prevCouponDate, currDate)


# Returns the days elapsed since last Coupon date
def getNextCouponDate(issueDate, maturityDate, frequency, holidayCities, settleDate):
    # first create a Sceduke of cashflows
    schedule = __createSchedule(pydate_to_qldate(issueDate), pydate_to_qldate(maturityDate),
                                frequency, holidayCities)
    nextCouponDate = [i for i in list(schedule) if i > pydate_to_qldate(settleDate)][0]
    return qldate_to_pydate(nextCouponDate)


# Returns the days elapsed since last Coupon date
def getLastCouponDate(issueDate, maturityDate, frequency, holidayCities, settleDate):
    # first create a Sceduke of cashflows
    schedule = __createSchedule(pydate_to_qldate(issueDate), pydate_to_qldate(maturityDate),
                                frequency, holidayCities)
    lastCouponDate = [i for i in list(schedule) if i < pydate_to_qldate(settleDate)][-1]
    return qldate_to_pydate(lastCouponDate)


if __name__ == "__main__":
    date = ql.Date(1, 1, 2017)
    us_calendar = ql.UnitedStates()
    italy_calendar = ql.Italy()

    period = ql.Period(60, ql.Days)
    raw_date = date + period
    us_date = us_calendar.advance(date, period)
    italy_date = italy_calendar.advance(date, period)

    print("Business Days=%s" % calculateBusDays("NY", py_sd=dt.datetime(2016, 12, 25), py_ed=dt.datetime(2016, 12, 28)))

    # Creating a Fixed Coupon Bond.....
    issueDate = ql.Date(17, 9, 2009)
    maturityDate = ql.Date(14, 9, 2022)
    tenor = ql.Period(ql.Semiannual)
    calendar = ql.UnitedStates()
    businessConvention = ql.Unadjusted
    dateGeneration = ql.DateGeneration.Backward
    monthEnd = False
    coupon = 0.05
    schedule = ql.Schedule(issueDate, maturityDate, tenor, calendar, businessConvention, businessConvention,
                           dateGeneration, monthEnd)
    bond = createFixedRateBond(issueDate, maturityDate, Frequency.ANNUAL,
                               HolidayCities.EUR, coupon,
                               DayCountConv.ACT_ACT)
    print("yield = %s" % ytm_given_price(bond, 124.019, Frequency.ANNUAL))
