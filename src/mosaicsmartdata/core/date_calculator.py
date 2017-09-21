#from mosaicsmartdata.core.instrument import TenorTuple
from datetime import timedelta
from QuantLib import *
from mosaicsmartdata.common.quantlib.bond.fixed_bond import *
from mosaicsmartdata.common.constants import *

class DateCalculatorBorg:
    _shared = {}
    def __init__(self):
        self.__dict__ = self._shared


class DateCalculator(DateCalculatorBorg):
    def __init__(self):
        super().__init__()
        self.intervals = set()

    def date_add(self, today, interval, holiday_cities = HolidayCities.NYC):
        calendar = HolidayCities.convert_holidayCities_str(holiday_cities)
        ql_today = pydate_to_qldate(today)
        end_date = None
        if not calendar.isBusinessDay(ql_today):
            ql_today = calendar.adjust(ql_today, ModifiedFollowing)
        if interval[-1].lower() == 'b': # really want to return the next BUSINESS DAY
            if float(interval[:-1]) == 0.0:
                # period = Period(1, Days)
                end_date = ql_today
            else:
                period = Period(int(interval[:-1]), Days)
                end_date = calendar.advance(ql_today, period)
            # days = float(interval[:-1])
        elif interval[-1].lower() =='m':
            period = Period(int(interval[:-1]), Months)
            end_date = calendar.advance(ql_today, period)
        elif interval[-1].lower() =='w':
            period = Period(int(interval[:-1]), Weeks)
            end_date = calendar.advance(ql_today, period)
        elif interval[-1].lower() == 'y':
            period = Period(int(interval[:-1]), Years)
            end_date = calendar.advance(ql_today, period)

        # delta = timedelta(days=days)
        return qldate_to_pydate(end_date)

        # self.intervals.add(interval)
        # print(self.intervals)


    def spot_date(self, instr_type, ccypair, today):
        # TODO: get holiday cities from ccypair/ccy
        if instr_type == 'ois':
            return self.date_add(today, '2b')
        elif instr_type == 'fx':
            if ccypair in [('USD', 'CAD'),
                           ('USD', 'TRY'),
                           ('USD', 'PHP'),
                           ('USD', 'RUB'),
                           ('USD', 'KZT'),
                           ('USD', 'PKR')]:
                delta = '1b'
            else:
                delta = '2b'
        else:
            raise ValueError("Can only hanlde instrument types fx and ois, got ",instr_type)
        return self.date_add(today, delta)

    def resolve_tenor(self, instr, today):
        # TODO: handle non-spot tenors
        # a bunch of cases, calculating the dates corresponding to the tenor for different instruments
        # if not isinstance(tenor_tuple, TenorTuple):
        #     raise ValueError('Expected a TenorTuple, got ', tenor_tuple)

        tenor = instr.tenor

        if tenor.lower() == 'spot':
            return self.spot_date(instr.ccy, today)