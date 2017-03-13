from decimal import *
import time, random
import datetime as dt
from .constants import *
import math
import numpy as np

class Quote:
    def __init__(self, instr , timestamp, bid, ask):
        self.instr = instr
        self.timestamp = float(timestamp)
        self.bid = float(bid)
        self.ask = float(ask)

    def mid(self):
        return 0.5*(self.ask+self.bid)

    def __str__(self):
        return 'QUOTE: instr:' + str(self.instr) + \
            ' timestamp:' + str(self.timestamp) + \
            ' bid:' + str(self.bid) + \
            ' ask:' + str(self.ask)

class Trade:
    def __init__(self, TradeId = None, instr = None,
                 timestamp = None, size = None,
                 Notional = None, Side = None, TradedPx = None,
                 ClientKey = None, TradeDate = None,
                 TradeSettleDate = None, TradeRC = None,
                 Sales = None, Trader = None
                 ):
        # properties of trade itself
        self.TradeId = TradeId
        self.instr = instr
        self.timestamp = timestamp
        self.size=size
        self.Notional = Notional
        self.Side = Side
        self.TradedPx = TradedPx
        self.ClientKey = ClientKey
        self.TradeDate = TradeDate
        self.TradeSettleDate = TradeSettleDate
        self.TradeRc = TradeRC  # revenue credits? Do JPM use them?
        self.Sales = Sales
        self.Trader = Trader

    def __str__(self):
        return 'TRADE: instr:' + str(self.instr) + \
               ' timestamp:' + str(self.timestamp) + \
               ' price:' + str(self.TradedPx) + \
               ' size:' + str(self.size)


class FixedIncomeTrade(Trade):
    # Attributes with default parameter.
    TradeId = ""
    IsBenchmark = False
    Notional = None
    Sym = None
    # Ccy = Currency.EUR
    BidPx = AskPx = MidPx = None
    ONRepo = None
    Duration = None
    TradeAddedToRP = False

    # Instrument Static
    Coupon = 0.02
    CouponFrequency = Frequency.SEMI
    DayCount = DayCountConv.ACT_365

    # Constructor
    def __init__(self, *varargin):

        if len(varargin) == 1:
            trade_in = varargin[0]
            # all properties that any trade can have belong in the superclass
            super().__init__( TradeId = trade_in[0],
                Notional = trade_in[2],
                Side = trade_in[3],
                TradedPx = trade_in[4],
                ClientKey = trade_in[7],
                TradeDate = trade_in[11],
                TradeSettleDate = trade_in[12],
                TradeRc = trade_in[13],  # revenue credits? Does everybody use them?
                Sales = trade_in[14],
                Trader = trade_in[15])
            # properties of the general instrument
            self.Sym = trade_in[1]
            self.IsBenchmark = trade_in[10]
            self.Ccy = trade_in[17]
            self.Tenor = trade_in[18]
            # instrument static
            self.IssueDate = trade_in[22]
            self.MaturityDate = trade_in[23]
            self.Coupon = trade_in[24]
            self.CouponFrequency = trade_in[25]
            self.DV01 = trade_in[19]  # DV01 of unit notional?
            self.Duration = trade_in[8]
            self.ONRepo = trade_in[9] # what does this mean?
            # properties of the instrument on that date
            self.SpotSettleDate = trade_in[20]
            # properties of last quote observed before trade?
            self.BidPx = trade_in[5]
            self.AskPx = trade_in[6]
            self.MidPx = np.mean(self.BidPx, self.AskPx)

            # what is that?
            self.RiskPathId = trade_in[21]
            self.MidPxTS = trade_in[16]  # key value pair
        else:
            self.ONRepo = math.nan

    def calculate_trade_dv01(self):
        self.DV01 = self.Duration * self.Notional * 0.0001
        # return tradeDV01

    def __str__(self):
        return "Trade: TradeId - %s, Sym - %s, TradeDate - %s, SpotSettleDate - %s, TradeSettleDate - %s, Side - %s, " \
               "TradedPx - %s, MidPx - %s, DV01 - %s" % \
               (self.TradeId, self.Sym, self.TradeDate, self.SpotSettleDate, self.TradeSettleDate,
                self.Side, self.TradedPx, self.MidPxTS["mid"], self.DV01)


if __name__ == '__main__':
    date_0 = dt.datetime(2017, 1, 2)
    time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
    tr = Trade()
    tr.TradeId = '111'
    tr.Sym = '9128235'
    tr.Notional = 7000000
    tr.Side = TradeSide.Bid
    tr.TradedPx = 96.916
    tr.MidPx = 96.928
    tr.ClientSysKey = 111
    tr.Duration = 8.92
    tr.ONRepo = 0.02
    tr.TradeDate = date_0
    tr.Ccy = 'EUR'
    tr.calculate_trade_dv01()
