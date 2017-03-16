import datetime as dt
import math

import numpy as np

from core.constants import *


class Quote:
    def __init__(self, sym, timestamp, bid, ask):
        self.sym = sym
        self.timestamp = timestamp # <-- should be in datetime format
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
    def __init__(self, trade_id=None, instr=None,
                 timestamp=None, size=None,
                 notional=None, side=None, traded_px=None,
                 client_sys_key=None, trade_date=None,
                 trade_settle_date=None, trade_rc=None,
                 sales=None, trader=None
                 ):
        # properties of trade itself
        self.trade_id = trade_id
        self.instr = instr
        self.timestamp = timestamp
        self.size = size
        self.notional = notional
        self.side = side
        self.traded_px = traded_px
        self.client_key = client_sys_key
        self.trade_date = trade_date
        self.trade_settle_date = trade_settle_date
        self.trade_rc = trade_rc  # revenue credits? Do JPM use them?
        self.sales = sales
        self.trader = trader

    @property
    def __str__(self):
        return 'TRADE: trade_id:' + str(self.trade_id) +\
               'instr:' + str(self.instr) + \
               ' timestamp:' + str(self.timestamp) + \
               ' price:' + str(self.traded_px) + \
               ' size:' + str(self.size)


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
    def __init__(self, *varargin):

        if len(varargin) == 1:
            trade_in = varargin[0]
            # all properties that any trade can have belong in the superclass
            Trade.__init__(trade_id=trade_in[0],
                             notional=trade_in[2],
                             side=trade_in[3],
                             traded_px=trade_in[4],
                             client_sys_key=trade_in[7],
                             trade_date=trade_in[11],
                             trade_settle_date=trade_in[12],
                             trade_rc=trade_in[13],  # revenue credits? Does everybody use them?
                             sales=trade_in[14],
                             trader=trade_in[15])
            # properties of the general instrument
            self.sym = trade_in[1]
            self.is_benchmark = trade_in[10]
            self.ccy = trade_in[17]
            self.tenor = trade_in[18]
            # instrument static
            self.issue_date = trade_in[22]
            self.maturity_date = trade_in[23]
            self.coupon = trade_in[24]
            self.coupon_frequency = trade_in[25]
            self.DV01 = trade_in[19]  # DV01 of unit notional?
            self.duration = trade_in[8]
            self.on_repo = trade_in[9]  # what does this mean?
            # properties of the instrument on that date
            self.spot_settle_date = trade_in[20]
            # properties of last quote observed before trade?
            self.bid_px = trade_in[5]
            self.ask_px = trade_in[6]
            self.mid_px = np.mean(self.bid_px, self.ask_px)

            # what is that?
            self.risk_path_id = trade_in[21]
            self.mid_px_ts = trade_in[16]  # key value pair
        else:
            self.on_repo = math.nan

    def calculate_trade_dv01(self):
        self.DV01 = self.duration * self.notional * 0.0001
        # return tradeDV01

    def __str__(self):
        return "Trade: TradeId - %s, Sym - %s, TradeDate - %s, SpotSettleDate - %s, TradeSettleDate - %s, Side - %s, " \
               "TradedPx - %s, MidPx - %s, DV01 - %s" % \
               (self.trade_id, self.sym, self.trade_date, self.spot_settle_date, self.trade_settle_date,
                self.side, self.traded_px, self.mid_px_ts["mid"], self.DV01)


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
    tr.calculate_trade_dv01()
