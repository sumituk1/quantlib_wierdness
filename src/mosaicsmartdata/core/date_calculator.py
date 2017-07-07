#from mosaicsmartdata.core.instrument import TenorTuple


class DateCalculatorBorg:
    _shared = {}
    def __init__(self):
        self.__dict__ = self._shared


class DateCalculator(DateCalculatorBorg):
    def __init__(self):
        super().__init__()

    def date_add(self, today, interval, holiday_cities = None):
        # TODO: call quantlib wrappers here
        # must support at least intervals of 0b (nearest business day), 1b, 2b,
        # and the standard tenors
        return today

    def spot_date(self, ccypair, today):
        # TODO: get holiday cities from ccypair
        if ccypair in [('USD', 'CAD'),
                       ('USD', 'TRY'),
                       ('USD', 'PHP'),
                       ('USD', 'RUB'),
                       ('USD', 'KZT'),
                       ('USD', 'PKR')]:
            delta = '1b'
        else:
            delta = '2b'
        return self.date_add(today, delta)

    def resolve_tenor(self, instr, today):
        # TODO: handle non-spot tenors
        # a bunch of cases, calculating the dates corresponding to the tenor for different instruments
        # if not isinstance(tenor_tuple, TenorTuple):
        #     raise ValueError('Expected a TenorTuple, got ', tenor_tuple)

        tenor = instr.tenor

        if tenor.lower() == 'spot':
            return self.spot_date(instr.ccy, today)