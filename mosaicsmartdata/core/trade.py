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

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        self.bid = float(self.bid)
        self.ask = float(self.ask)

    def mid(self):
        return 0.5*(self.bid+self.ask)




class Trade(GenericParent):
    def __init__(self, *args, **kwargs):
        self.trade_id = None
        self.parent_id = None
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

        if self.parent_id is None:
            self.parent_id = self.trade_id

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

if False:
    class Trade:
        def __init__(self, trade_id, sym,
                     timestamp,
                     notional,
                     side,
                     traded_px,
                     trade_date,
                     trade_settle_date,
                     ccy=Currency.EUR,
                     client_sys_key=None,
                     trade_rc=None,
                     sales=None,
                     trader=None,
                     delta=None
                     ):
            # properties of trade itself
            self.trade_id = trade_id
            self.sym = sym
            self.timestamp = timestamp
            self.notional = notional
            self.side = side
            self.traded_px = traded_px
            self.client_key = client_sys_key
            self.trade_date = trade_date
            self.trade_settle_date = trade_settle_date
            self.trade_rc = trade_rc  # revenue credits? Do JPM use them?
            self.sales = sales
            self.trader = trader
            self.delta = delta
            self.ccy = ccy

        def __str__(self):
            return 'TRADE: trade_id:' + str(self.trade_id) + \
                   'instr:' + str(self.sym) + \
                   ' timestamp:' + str(self.timestamp) + \
                   ' price:' + str(self.traded_px) + \
                   ' size:' + str(self.notional)


    class FixedIncomeTrade(Trade):
        # Attributes with default parameter.
        trade_id = ""
        is_benchmark = False
        notional = None
        sym = None
        bid_px = ask_px = mid_px = None
        on_repo = None
        duration = None
        trade_added_to_rp = False
        is_d2d_force_close = False
        # # Instrument Static
        # coupon = 0.02
        # coupon_frequency = Frequency.SEMI
        # day_count = DayCountConv.ACT_365

        # Constructor
        def __init__(self, trade_id, sym,
                     timestamp,
                     notional,
                     side,
                     traded_px,
                     trade_date,
                     trade_settle_date,
                     duration,
                     ccy=Currency.EUR,
                     par_value=100,
                     client_sys_key=None,
                     trade_rc=None,
                     sales=None,
                     trader=None,
                     delta=None,
                     spot_settle_date=None,
                     issue_date=None,
                     maturity_date=None,
                     coupon=None,
                     coupon_frequency=None):
            # all properties that any trade can have belong in the superclass
            Trade.__init__(self, trade_id=trade_id,
                           timestamp=timestamp,
                           sym=sym,
                           notional=notional,
                           side=side,
                           traded_px=traded_px,
                           client_sys_key=client_sys_key,
                           trade_date=trade_date,
                           trade_settle_date=trade_settle_date,
                           # trade_rc=7,  # revenue credits? Does everybody use them?
                           sales=sales,
                           trader=trader,
                           ccy=ccy)

            # properties of the general instrument
            self.trade_rc = trade_rc
            self.duration = duration
            self.is_benchmark = False

            self.calculate_trade_delta(delta)
            # instrument static
            self.par_value = par_value
            self.issue_date = issue_date
            self.maturity_date = maturity_date
            self.coupon = coupon
            self.coupon_frequency = coupon_frequency
            self.spot_settle_date = spot_settle_date
            # self.on_repo = trade_in[9]  # what does this mean?
            # properties of the instrument on that date


            # # properties of last quote observed before trade?
            # self.bid_px = trade_in[5]
            # self.ask_px = trade_in[6]
            # self.mid_px = np.mean(self.bid_px, self.ask_px)

            # what is that?
            # self.risk_path_id = trade_in[21]
            # self.mid_px_ts = trade_in[16]  # key value pair

        def calculate_trade_delta(self, delta):
            if delta is None:
                self.delta = self.duration * self.notional * 0.0001
            else:
                self.delta = delta

        def __str__(self):
            return 'TRADE: trade_id:' + str(self.trade_id) + \
                   ' instr:' + str(self.sym) + \
                   ' timestamp:' + str(self.timestamp) + \
                   ' price:' + str(self.traded_px) + \
                   ' size:' + str(self.notional)


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
