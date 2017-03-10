from decimal import *
import time, random
import datetime as dt
from constants import *
import math
import numpy as np

class Trade:
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
            self.TradeId = trade_in[0]
            self.Sym = trade_in[1]
            self.Notional = trade_in[2]
            self.Side = trade_in[3]
            self.TradedPx = trade_in[4]
            self.BidPx = trade_in[5]
            self.AskPx = trade_in[6]
            self.MidPx = np.mean(self.BidPx, self.AskPx)
            self.ClientKey = trade_in[7]
            self.Duration = trade_in[8]
            self.ONRepo = trade_in[9]
            self.IsBenchmark = trade_in[10]
            self.TradeDate = trade_in[11]
            self.TradeSettleDate = trade_in[12]
            self.TradeRc = trade_in[13]
            self.Sales = trade_in[14]
            self.Trader = trade_in[15]
            self.MidPxTS = trade_in[16]  # key value pair
            self.Ccy = trade_in[17]
            self.Tenor = trade_in[18]
            self.DV01 = trade_in[19]
            self.SpotSettleDate = trade_in[20]
            self.RiskPathId = trade_in[21]
            # instrument static
            self.IssueDate = trade_in[22]
            self.MaturityDate = trade_in[23]
            self.Coupon = trade_in[24]
            self.CouponFrequency = trade_in[25]

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
