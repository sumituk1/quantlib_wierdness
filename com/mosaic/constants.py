# This has the list of day counts and the related convention
# from workalendar.usa import *
import QuantLib as ql

class BootStrapMethod:
    PiecewiseLogCubicDiscount = "PicewiseLogCubicDiscount"
    PiecewiseFlatForward = "PiecewiseFlatForward"

class DayCountConv:
    ACT_ACT = "ACT/ACT"
    ACT_ACT_ISDA = "ACT/ACT(ISDA)"
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    ACT_365L = "ACT/365L"
    ACT_252 = "ACT/252" # -> Business252 in Quantlib

    BASIC30_360 = "BASIC30/360"
    NASD30_360 = "NASD30/360"

    Thirty360 = "30/360" # -> Thirty360:
    Thirty360_US = "30/360 US"  # -> Thirty360:
    ThirtyE360 = "30E/360"  # -> Thirty360:

    @staticmethod
    def convertDayCountStr(dayCountStr):
        dcf = DayCountConv.ACT_ACT
        if dayCountStr == "ACT/ACT":
            dcf = DayCountConv.ACT_ACT
        elif dayCountStr == "ACT/ACT(ISDA)":
            dcf = DayCountConv.ACT_ACT_ISDA
        elif dayCountStr == "ACT/360":
            dcf = DayCountConv.ACT_360
        elif dayCountStr == "ACT/365":
            dcf = DayCountConv.ACT_365
        elif dayCountStr == "ACT/365L":
            dcf = DayCountConv.ACT_365L
        elif dayCountStr == "ACT/252":
            dcf = DayCountConv.ACT_252
        elif dayCountStr == "BASIC30/360":
            dcf = DayCountConv.BASIC30_360
        elif dayCountStr == "NASD30/360":
            dcf = DayCountConv.NASD30_360
        elif dayCountStr == "30/360 US":
            dcf = DayCountConv.Thirty360_US
        return	dcf

class Frequency:
    MONTHLY = "M"
    DAILY = "D"
    WEEKLY = "W"
    SEMI = "S"
    QUARTERLY = "Q"
    ANNUAL = "A"

    @staticmethod
    def convertFrequencyStr(freqStr):
        freq = Frequency.SEMI
        if freqStr == "M":
            freq = Frequency.MONTHLY
        elif freqStr == "D":
            freq = Frequency.DAILY
        elif freqStr == "W":
            freq = Frequency.WEEKLY
        elif freqStr == "S":
            freq = Frequency.SEMI
        elif freqStr == "Q":
            freq = Frequency.QUARTERLY
        elif freqStr == "A":
            freq = Frequency.ANNUAL
        return freq

    @staticmethod
    def getFrequencyNumber(freqStr):
        freqNumberOut = 1 #<-- default to annual
        if freqStr == Frequency.MONTHLY:
            freqNumberOut = 12
        elif freqStr == Frequency.DAILY:
            freqNumberOut = 365
        elif freqStr == Frequency.WEEKLY:
            freqNumberOut = 52
        elif freqStr == Frequency.SEMI:
            freqNumberOut = 2
        elif freqStr == Frequency.QUARTERLY:
            freqNumberOut = 4
        elif freqStr == Frequency.ANNUAL:
            freqNumberOut = 1
        return freqNumberOut

    @staticmethod
    def getQLFrequency(freqStr):
        freqStrOut = ql.Semiannual
        if freqStr == Frequency.MONTHLY:
            freqStrOut = ql.Monthly
        elif freqStr == Frequency.DAILY:
            freqStrOut = ql.Daily
        elif freqStr == Frequency.WEEKLY:
            freqStrOut = ql.Weekly
        elif freqStr == Frequency.SEMI:
            freqStrOut = ql.Semiannual
        elif freqStr == Frequency.QUARTERLY:
            freqStrOut = ql.Quarterly
        elif freqStr == Frequency.ANNUAL:
            freqStrOut = ql.Annual
        return freqStrOut

class CalendarFactory:
    def __init__(self):
        self.map ={"USA": "UnitedStates","FRA": "France","GRE": "Greece","GBR": "UnitedKingdom"}

    def get(self, countryISO):
        return eval("%s()" % self.map[countryISO])

class HolidayCities:
    USA = "NY"
    GBP = "LON"
    EUR = "EUR"
    JPY = "TOK"
    IT = "ITALY"
    TARGET = "TARGET"
    ISR = "ISRAEL"
    CHINA = "BEJ"

class Currency:
    EUR = "EUR"
    USD = "USD"
    CAD = "CAD"
    JPY = "JPY"
    AUD = "AUD"
    NZD = "NZD"
    GBP = "GBP"
    CHF = "CHF"
    SEK = "SEK"
    NOK = "NOK"
    CNH = "CNH"
    CNY = "CNY"
    BRL = "BRL"
    MXN = "MXN"
    RUB = "RUB"
    INR = "INR"
    SGD = "SGD"
    THB = "THB"


class TradeSide:
    Bid = "B"
    Ask = "A"