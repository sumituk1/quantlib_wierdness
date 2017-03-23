import datetime as dt

from mosaicsmartdata.common.constants import *

class GenericParent:
    def __init__(self, *args, **kwargs):
        if len(kwargs):
            raise ValueError('Unknown arguments:', kwargs)

    def apply_kwargs(self, goodargs, kwargs):
        # print('Entering apply_kwargs', self, goodargs, kwargs)

        other_kwargs = {key: value for key, value in kwargs.items() if key not in goodargs}
        good_kwargs = {key: value for key, value in kwargs.items() if key in goodargs}

        for key, value in good_kwargs.items():
            self.__dict__[key] = value

        return other_kwargs

    def check_values(self, names):
        for x in names:
            if self.__dict__[x] is None:
                raise ValueError(x + ' must be specified')

    def __str__(self):
        my_string = str(type(self)) + ' : '
        for key, value in self.__dict__.items():
            my_string = my_string + ', ' + key + ' = ' + str(value)
        my_string = my_string.replace(': ,', ': ')
        return my_string


# convert a class with a simple structure to a dict
def to_dict(x):
    my_dict = x.__dict__
    my_dict['_class'] = str(type(x)).replace('\'', '').replace('>', '').split('.')[-1]
    return my_dict

# reflate the class back from a dict
def from_dict(x):
    atype = globals()[x.pop('_class')]
    return atype(**x)


class Quote(GenericParent):
    def __init__(self, *args, **kwargs):
        self.sym = None
        self.timestamp = None  # <-- should be in datetime format
        self.bid = None
        self.ask = None
        self.duration = None # <-- need this for hedging

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        self.bid = float(self.bid)
        self.ask = float(self.ask)
        self.duration = float(self.duration) if self.duration is not None else None

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        # calculate different markout types on the fly by applying the correct multiplier
        elif str(item) == 'mid':
            return 0.5*(self.bid + self.ask)
        else:
            raise ValueError('This object doesn\'t have attribute \"' + item + '\"' )


class Trade(GenericParent):
    def __init__(self, *args, **kwargs):
        self.trade_id = None
        self.package_id = None
        self.paper_trade = False
        self.sym = None
        self.timestamp = None
        self.notional = None
        self.side = None
        self.traded_px = None
        self.trade_date = None
        self.trade_settle_date = None
        self.ccy=Currency.EUR
        self.client_sys_key = None
        self.trade_rc = None
        self.sales = None
        self.trader = None
        self.delta = None

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        # use this syntax to require non-None values for certain fields
        self.check_values(['trade_id'])

        if self.package_id is None:
            self.package_id = self.trade_id

        def markout_mults(self):
            return {'price': 1, 'PV': self.delta}

class FixedIncomeTrade(Trade):
    # Attributes with default parameter.
    # # Instrument Static
    # coupon = 0.02
    # coupon_frequency = Frequency.SEMI
    # day_count = DayCountConv.ACT_365

    # Constructor
    def __init__(self, *args, **kwargs):
        self.is_benchmark = False
        self.bid_px = None
        self.ask_px = None
        self.mid_px = None
        self.on_repo = None
        self.duration = None
        self.trade_added_to_rp = False
        self.is_d2d_force_close = False
        self.duration = None
        self.par_value = 100
        self.spot_settle_date = None
        self.issue_date = None
        self.maturity_date = None
        self.coupon = None
        self.coupon_frequency = None

        # the magic line to process the kwargs
        # other_args = self.apply_kwargs(self.__dict__,kwargs)
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        if self.delta is None:
            self.delta = self.duration * self.notional * 0.0001


    def markout_mults(self):
        return {'price': 1,
                'PV': self.delta,
                'cents': 100.0,
                'bps':(1.0 / self.duration / self.par_value) * 10000}

if __name__ == '__main__':
    date_0 = dt.datetime(2017, 1, 2)
    time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
    tr = Trade()
    tr.trade_id = '111'
    tr.sym = '9128235'
    tr.notional = 7000000
    tr.side = TradeSide.Bid
    tr.traded_px = 96.916
    tr.mid_px = 96.928
    tr.client_key = 111
    tr.duration = 8.92
    tr.on_repo = 0.02
    tr.trade_date = date_0
    tr.ccy = 'EUR'
    # tr.calculate_trade_dv01()
