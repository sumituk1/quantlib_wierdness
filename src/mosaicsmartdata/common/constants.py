# This has the list of day counts and the related convention
# from workalendar.usa import *
import QuantLib as ql
from QuantLib import *
from enum import Enum

class BootStrapMethod:
    PiecewiseLogCubicDiscount = "PicewiseLogCubicDiscount"
    PiecewiseFlatForward = "PiecewiseFlatForward"

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

