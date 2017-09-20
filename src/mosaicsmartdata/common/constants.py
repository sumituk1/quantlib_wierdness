# This has the list of day counts and the related convention
# from workalendar.usa import *
from QuantLib import *
from enum import Enum

class BootStrapMethod:
    PiecewiseLogCubicDiscount = "PicewiseLogCubicDiscount"
    PiecewiseFlatForward = "PiecewiseFlatForward"


class MarkoutMode:
    Unhedged = 1
    Hedged = 2


class DayCountConv:
    ACT_ACT = "ACT/ACT"
    ACT_ACT_ISDA = "ACT/ACT(ISDA)"
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    ACT_365L = "ACT/365L"
    ACT_252 = "ACT/252"  # -> Business252 in Quantlib

    BASIC30_360 = "BASIC30/360"
    NASD30_360 = "NASD30/360"

    Thirty360 = "30/360"  # -> Thirty360:
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
        return dcf


class CalendarFactory:
    def __init__(self):
        self.map = {"USA": "UnitedStates", "FRA": "France", "GRE": "Greece", "GBR": "UnitedKingdom"}

    def get(self, countryISO):
        return eval("%s()" % self.map[countryISO])


class HolidayCities(Enum):
    NYC,USD = 1,1
    GBP,LON = 2,2
    NYC_LON = 3
    EUR,TARGET = 4,4
    AUSTRALIA = 5
    ARGENTINA = 6
    BRAZIL = 7
    CANADA = 8
    CHINA = 9
    CZECHREPUBLIC = 10
    DENMARK = 11
    FINLAND = 12
    GERMANY = 13
    HONGKONG = 14
    HUNGARY = 15
    ICELAND = 16
    ISR,ISRAEL = 17, 17
    IT,ITALY = 18,18
    INDIA = 19
    INDONESIA = 20
    JPY,JAPAN = 21,21
    NEWZEALAND = 22
    NORWAY = 23
    NYC_EUR = 24
    POLAND = 25
    RUSSIA = 26
    SWITZERLAND = 27
    SINGAPORE = 28
    SOUTHAFRICA = 29
    TAIWAN = 30
    TOK = 31
    TURKEY = 32
    UNITEDSTATES = 33
    UNITEDKINGDOM = 34
    SWEDEN = 35
    ROMANIA = 36
    SOUTHKOREA = 37


    @staticmethod
    def convert_holidayCities_str(holiday_cities):
        if isinstance(holiday_cities, str):
            holiday_cities = HolidayCities[holiday_cities] ## covert to enum type
        if holiday_cities == HolidayCities.LON:
            holiday_cities = UnitedKingdom()
        elif holiday_cities == HolidayCities.NYC or holiday_cities == HolidayCities.USD:
            holiday_cities = UnitedStates()
        elif holiday_cities == HolidayCities.NYC_LON:
            holiday_cities = JointCalendar(UnitedStates(),UnitedKingdom())
        elif holiday_cities == HolidayCities.EUR or holiday_cities == HolidayCities.TARGET:
            holiday_cities = TARGET()
        elif holiday_cities == HolidayCities.AUSTRALIA:
            holiday_cities = Australia()
        elif holiday_cities == HolidayCities.ARGENTINA:
            holiday_cities = Argentina()
        elif holiday_cities == HolidayCities.Brazil:
            holiday_cities = Brazil()
        elif holiday_cities == HolidayCities.CANADA:
            holiday_cities = Canada()
        elif holiday_cities == HolidayCities.CHINA:
            holiday_cities = China()
        elif holiday_cities == HolidayCities.CZECHREPUBLIC:
            holiday_cities = CzechRepublic()
        elif holiday_cities == HolidayCities.DENMARK:
            holiday_cities = Denmark()
        elif holiday_cities == HolidayCities.FINLAND:
            holiday_cities = Finland()
        elif holiday_cities == HolidayCities.GERMANY:
            holiday_cities = Germany()
        elif holiday_cities == HolidayCities.HONGKONG:
            holiday_cities = HongKong()
        elif holiday_cities == HolidayCities.HUNGARY:
            holiday_cities = Hungary()
        elif holiday_cities == HolidayCities.ICELAND:
            holiday_cities = Iceland()
        elif holiday_cities == HolidayCities.ISRAEL or holiday_cities == HolidayCities.ISR:
            holiday_cities = Israel()
        elif holiday_cities == HolidayCities.ITALY or holiday_cities == HolidayCities.IT:
            holiday_cities = Italy()
        elif holiday_cities == HolidayCities.INDIA:
            holiday_cities = India()
        elif holiday_cities == HolidayCities.INDONESIA:
            holiday_cities = Indonesia()
        elif holiday_cities == HolidayCities.JAPAN or holiday_cities == HolidayCities.JPY:
            holiday_cities = Japan()
        elif holiday_cities == HolidayCities.NEWZEALAND:
            holiday_cities = NewZealand()
        elif holiday_cities == HolidayCities.NORWAY:
            holiday_cities = Norway()
        elif holiday_cities == HolidayCities.NYC_EUR:
            holiday_cities = JointCalendar(UnitedStates(), TARGET())
        elif holiday_cities == HolidayCities.POLAND:
            holiday_cities = Poland()
        elif holiday_cities == HolidayCities.RUSSIA:
            holiday_cities = Russia()
        elif holiday_cities == HolidayCities.ROMANIA:
            holiday_cities = Romania()
        elif holiday_cities == HolidayCities.SWITZERLAND:
            holiday_cities = Switzerland()
        elif holiday_cities == HolidayCities.SINGAPORE:
            holiday_cities = Singapore()
        elif holiday_cities == HolidayCities.SOUTHAFRICA:
            holiday_cities = SouthAfrica()
        elif holiday_cities == HolidayCities.SOUTHKOREA:
            holiday_cities = SouthKorea()
        elif holiday_cities == HolidayCities.TAIWAN:
            holiday_cities = Taiwan()
        elif holiday_cities == HolidayCities.TOK:
            holiday_cities = Japan()
        elif holiday_cities == HolidayCities.TURKEY:
            holiday_cities = Turkey()
        elif holiday_cities == HolidayCities.UNITEDSTATES:
            holiday_cities = UnitedStates()
        elif holiday_cities == HolidayCities.UNITEDKINGDOM or holiday_cities == HolidayCities.GBP:
            holiday_cities = UnitedKingdom()
        elif holiday_cities == HolidayCities.SWEDEN:
            holiday_cities = Sweden()
        else:
            holiday_cities = HolidayCities.NYC_LON
        return holiday_cities

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


class Country:
    AF = 1,
    AX = 2,
    AL = 3,
    DZ = 4,
    AS = 5,
    AD = 6,
    AO = 7,
    AI = 8,
    AQ = 9,
    AG = 10,
    AR = 11,
    AM = 12,
    AW = 13,
    AU = 14,
    AT = 15,
    AZ = 16,
    BS = 17,
    BH = 18,
    BD = 19,
    BB = 20,
    BY = 21,
    BE = 22,
    BZ = 23,
    BJ = 24,
    BM = 25,
    BT = 26,
    BO = 27,
    BQ = 28,
    BA = 29,
    BW = 30,
    BV = 31,
    BR = 32,
    IO = 33,
    BN = 34,
    BG = 35,
    BF = 36,
    BI = 37,
    KH = 38,
    CM = 39,
    CA = 40,
    CV = 41,
    KY = 42,
    CF = 43,
    TD = 44,
    CL = 45,
    CN = 46,
    CX = 47,
    CC = 48,
    CO = 49,
    KM = 50,
    CG = 51,
    CD = 52,
    CK = 53,
    CR = 54,
    CI = 55,
    HR = 56,
    CU = 57,
    CW = 58,
    CY = 59,
    CZ = 60,
    DK = 61,
    DJ = 62,
    DM = 63,
    DO = 64,
    EC = 65,
    EG = 66,
    SV = 67,
    GQ = 68,
    ER = 69,
    EE = 70,
    ET = 71,
    FK = 72,
    FO = 73,
    FJ = 74,
    FI = 75,
    FR = 76,
    GF = 77,
    PF = 78,
    TF = 79,
    GA = 80,
    GM = 81,
    GE = 82,
    DE = 83,
    GH = 84,
    GI = 85,
    GR = 86,
    GL = 87,
    GD = 88,
    GP = 89,
    GU = 90,
    GT = 91,
    GG = 92,
    GN = 93,
    GW = 94,
    GY = 95,
    HT = 96,
    HM = 97,
    VA = 98,
    HN = 99,
    HK = 100,
    HU = 101,
    IS = 102,
    IN = 103,
    ID = 104,
    IR = 105,
    IQ = 106,
    IE = 107,
    IM = 108,
    IL = 109,
    IT = 110,
    JM = 111,
    JP = 112,
    JE = 113,
    JO = 114,
    KZ = 115,
    KE = 116,
    KI = 117,
    KP = 118,
    KR = 119,
    KW = 120,
    KG = 121,
    LA = 122,
    LV = 123,
    LB = 124,
    LS = 125,
    LR = 126,
    LY = 127,
    LI = 128,
    LT = 129,
    LU = 130,
    MO = 131,
    MK = 132,
    MG = 133,
    MW = 134,
    MY = 135,
    MV = 136,
    ML = 137,
    MT = 138,
    MH = 139,
    MQ = 140,
    MR = 141,
    MU = 142,
    YT = 143,
    MX = 144,
    FM = 145,
    MD = 146,
    MC = 147,
    MN = 148,
    ME = 149,
    MS = 150,
    MA = 151,
    MZ = 152,
    MM = 153,
    NA = 154,
    NR = 155,
    NP = 156,
    NL = 157,
    NC = 158,
    NZ = 159,
    NI = 160,
    NE = 161,
    NG = 162,
    NU = 163,
    NF = 164,
    MP = 165,
    NO = 166,
    OM = 167,
    PK = 168,
    PW = 169,
    PS = 170,
    PA = 171,
    PG = 172,
    PY = 173,
    PE = 174,
    PH = 175,
    PN = 176,
    PL = 177,
    PT = 178,
    PR = 179,
    QA = 180,
    RE = 181,
    RO = 182,
    RU = 183,
    RW = 184,
    BL = 185,
    SH = 186,
    KN = 187,
    LC = 188,
    MF = 189,
    PM = 190,
    VC = 191,
    WS = 192,
    SM = 193,
    ST = 194,
    SA = 195,
    SN = 196,
    RS = 197,
    SC = 198,
    SL = 199,
    SG = 200,
    SX = 201,
    SK = 202,
    SI = 203,
    SB = 204,
    SO = 205,
    ZA = 206,
    GS = 207,
    SS = 208,
    ES = 209,
    LK = 210,
    SD = 211,
    SR = 212,
    SJ = 213,
    SZ = 214,
    SE = 215,
    CH = 216,
    SY = 217,
    TW = 218,
    TJ = 219,
    TZ = 220,
    TH = 221,
    TL = 222,
    TG = 223,
    TK = 224,
    TO = 225,
    TT = 226,
    TN = 227,
    TR = 228,
    TM = 229,
    TC = 230,
    TV = 231,
    UG = 232,
    UA = 233,
    AE = 234,
    GB = 235,
    US = 236,
    UM = 237,
    UY = 238,
    UZ = 239,
    VU = 240,
    VE = 241,
    VN = 242,
    VG = 243,
    VI = 244,
    WF = 245,
    EH = 246,
    YE = 247,
    ZM = 248,
    ZW = 249


class TradeSide:
    Bid = "B"
    Ask = "A"


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
        if freqStr == "M" or freqStr == "MONTHLY":
            freq = Frequency.MONTHLY
        elif freqStr == "D"or freqStr == "DAILY":
            freq = Frequency.DAILY
        elif freqStr == "W"or freqStr == "WEEKLY":
            freq = Frequency.WEEKLY
        elif freqStr == "S"or freqStr == "SEMI":
            freq = Frequency.SEMI
        elif freqStr == "Q" or freqStr == "QUARTERLY":
            freq = Frequency.QUARTERLY
        elif freqStr == "A" or freqStr == "ANNUAL":
            freq = Frequency.ANNUAL
        return freq

    @staticmethod
    def getFrequencyNumber(freqStr):
        freqNumberOut = 1  # <-- default to annual
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

    try:
        import QuantLib as ql
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
    except:
        print("Didn't find Quantlib, so can't define Frequency.getQLFrequency")

class ProductClass(Enum):
    # def __str__(self):
    #     return str(self.value)

    GovtBond = 1
    CorpBond = 2
    Swaps = 3
    FXSpot = 4
    FXForwards = 5
    FXNDF = 6
    BondFutures = 7

'''This captures the type of RFQ deal. Possible values being:
-Upfront (this is for off-market. The traded_px will have the upfront fee)
-Basis ( This is the basis quoted for a basis swap or the spread quoted on the package leg of a Swap Spread)
-Price (typically on the outright legs)
-Spread (typically on the package leg)
-Discount ( typically the Bond leg of a Swap spread) - Will be excluded from Swap calculator
'''
class PriceType:
    Upfront = 1
    Basis = 2
    Price = 3
    Spread = 4
    Discount = 5

    @staticmethod
    def convert_price_type(price_type_str):
        # dcf = DayCountConv.ACT_ACT
        if str.upper(price_type_str) == "UPFRONT":
            return PriceType.Upfront
        elif str.upper(price_type_str) == "BASIS":
            return PriceType.Basis
        elif str.upper(price_type_str) == "PRICE":
            return PriceType.Price
        elif str.upper(price_type_str) == "SPREAD":
            return PriceType.Spread
        elif str.upper(price_type_str) == "DISCOUNT":
            return PriceType.Discount
