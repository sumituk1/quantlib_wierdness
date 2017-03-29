import datetime as dt
import numpy as np
from mosaicsmartdata.common import read_config
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
        self.duration = None  # <-- need this for hedging

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
            return 0.5 * (self.bid + self.ask)
        else:
            if str(item) not in ['__deepcopy__', '__getstate__']:
                raise ValueError('This object doesn\'t have attribute \"' + item + '\"')


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
        self.ccy = Currency.EUR
        self.client_sys_key = None
        self.trade_rc = None
        self.sales = None
        self.trader = None
        self.delta = None
        self.tenor = None
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
        self.beta = dict()  # for hedging using multiple assets
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
                'bps': (1.0 / self.duration / self.par_value) * 10000}

    def __str__(self):
        my_string = str(type(self)) + ' : '
        for key, value in self.__dict__.items():
            my_string = my_string + ', ' + key + ' = ' + str(value)
        my_string = my_string.replace(': ,', ': ')
        return my_string


class FixedIncomeFuturesHedge(Trade):
    def __init__(self, *args, **kwargs):
        # self.package_id = None
        self.min_hedge_delta = 1000  # in relevant ccy
        # self.trade = None
        self.duration = None # <- hedge trade attribute for the time being
        self.trade_delta = None # <- hedge trade_delta attribute for the time being
        self.trade_beta = dict()

        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.notional = 100000  # for futures
        self.paper_trade = True
        self.hedge_contracts = 0
        # self.notional = 0.0

        # Futures delta should always be passed in
        # if self.delta is None:
        #     # futures delta should always be passed in
        #     self.delta = self.duration * self.notional * 0.0001
        # self.package_id = None
        # self.trade_beta = dict()
        # self.trade_delta = None
        self.calculate_hedge_contracts()
        self.calculate_initial_hedge_cost()

    # def __call__(self):
    #     self.calculate_hedge_contracts()
    #     self.calculate_initial_hedge_cost()

    def calculate_hedge_contracts(self):
        if self.trade_delta > self.min_hedge_delta:
            create_hedge = True
        else:
            create_hedge = False
        if create_hedge:
            if not self.trade_beta:
                raise ValueError("Futures Hedge calculation called on trade with no hedges set")
            self.hedge_contracts = self.trade_beta[self.sym] * self.trade_delta / self.delta

    def calculate_initial_hedge_cost(self):
        if not self.trade_beta:
            raise ValueError("Futures Hedge calculation called on trade with no hedges set")
        self.notional *= self.hedge_contracts


"""
Handle OTC related hedge calcs
"""


class FixedIncomeOTCHedge(Trade):
    def __init__(self, *args, **kwargs):
        # self.package_id = None
        self.min_hedge_delta = 1000  # in relevant ccy
        # self.trade = None
        self.duration = None # <- hedge duration attribute for the time being
        self.trade_delta = None # <- hedge trade_delta attribute for the time being
        self.trade_beta = dict()

        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.notional = 1  # for OTC bonds
        self.paper_trade = True
        self.hedge_contracts = 0.0
        # self.notional = 0.0
        # self.traded_px = None
        # set delta of hedge instrument
        if self.delta is None:
            # futures delta should always be passed in
            self.delta = self.duration * self.notional * 0.0001
        # self.package_id = self.trade.package_id
        self.calculate_hedge_contracts()
        self.calculate_initial_hedge_cost()

    # def __call__(self):
    #     self.calculate_hedge_contracts()
    #     self.calculate_initial_hedge_cost()

    def calculate_hedge_contracts(self):
        if self.trade_delta > self.min_hedge_delta:
            create_hedge = True
        else:
            create_hedge = False
        if create_hedge:
            if not self.trade_beta:
                raise ValueError("OTC Hedge calculation called on trade with no hedges set")
            self.hedge_contracts = self.trade_beta[self.sym] * self.trade_delta / self.delta

    def calculate_initial_hedge_cost(self):
        if not self.trade_beta:
            raise ValueError("Futures Hedge calculation called on trade with no hedges set")
        self.notional *= self.hedge_contracts


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
