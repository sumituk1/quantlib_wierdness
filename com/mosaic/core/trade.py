import datetime as dt
import math
import numpy as np
from com.mosaic.core.constants import *


class Quote:
    def __init__(self, sym, timestamp, bid, ask):
        self.sym = sym
        self.timestamp = timestamp  # <-- should be in datetime format
        self.bid = float(bid)
        self.ask = float(ask)

    def mid(self):
        return 0.5 * (self.ask + self.bid)

    def __str__(self):
        return 'QUOTE: instr:' + str(self.sym) + \
               ' timestamp:' + str(self.timestamp) + \
               ' bid:' + str(self.bid) + \
               ' ask:' + str(self.ask)


class Trade:
    def __init__(self, trade_id, sym,
                 timestamp,
                 notional,
                 side,
                 traded_px,
                 trade_date,
                 trade_settle_date,
                 ccy = Currency.EUR,
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

    @property
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
    # Ccy = Currency.EUR
    bid_px = ask_px = mid_px = None
    on_repo = None
    duration = None
    trade_added_to_rp = False
    is_d2d_force_close = False
    # Instrument Static
    coupon = 0.02
    coupon_frequency = Frequency.SEMI
    day_count = DayCountConv.ACT_365

    # Constructor
    def __init__(self, trade_id, sym,
                 timestamp,
                 notional,
                 side,
                 traded_px,
                 trade_date,
                 trade_settle_date,
                 duration,
                 ccy = Currency.EUR,
                 client_sys_key=None,
                 trade_rc=None,
                 sales=None, trader=None, delta=None,
                 spot_settle_date=None, issue_date=None, maturity_date=None,coupon=None,coupon_frequency=None):
        # all properties that any trade can have belong in the superclass
        Trade.__init__(self,trade_id=trade_id,
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
        self.trade_rc= trade_rc
        self.duration = duration
        self.is_benchmark = False

        self.calculate_trade_delta(delta)
        # instrument static
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
