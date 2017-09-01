#from mosaicsmartdata.core.instrument import TenorTuple
from datetime import timedelta

class DateCalculatorBorg:
    _shared = {}
    def __init__(self):
        self.__dict__ = self._shared


class DateCalculator(DateCalculatorBorg):
    def __init__(self):
        super().__init__()
        self.intervals = set()

    def date_add(self, today, interval, holiday_cities = None):
        # TODO: call quantlib wrappers here instead
        if interval[-1].lower() == 'b': # really want to return the next BUSINESS DAY
            days = float(interval[:-1])
        elif interval[-1].lower() =='m':
            days = 30*float(interval[:-1])
        elif interval[-1].lower() =='w':
            days = 7*float(interval[:-1])
        elif interval[-1].lower() == 'y':
            days = 365* float(interval[:-1])

        delta = timedelta(days=days)
        return today + delta

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