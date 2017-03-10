from decimal import *
# from common.read_config import *
# from common.constants import TradeSide
# from pricing import trade
import time, random
import trade as trade
import datetime as dt
import numpy as np
from constants import *
import math


class Hedge:
    # MinHedgeDV01 = float(get_data_given_section_and_key("Rates-RiskPath", "MinHedgeDV01"))
    IsFutures = False
    Beta = 0.0

    def __init__(self, *varargin):

        if len(varargin) == 1:

            hedge_in = varargin[0]
            # self.TradedSym = hedge_in[0]
            self.BidPx = hedge_in[1]
            self.AskPx = hedge_in[2]
            self.MidPx = hedge_in[3]
            self.Beta = hedge_in[4]
            if self.Beta is None:
                self.Beta = 1.0
            self.DV01 = hedge_in[5]
            # self.tradeDV01 = hedge_in[6]
            self.IsFutures = hedge_in[6]
            self.HedgeContracts = hedge_in[7]
            if self.IsFutures:
                self.HedgeNotional = hedge_in[8]
            else:
                self.HedgeNotional = 1

            self.HedgePxTS = hedge_in[9]
            self.SovRisk = hedge_in[10]
            self.TradeObj = hedge_in[11]
            self.Sym = self.TradeObj.Sym
            self.calculate_hedge_contracts()
        else:
            # no contructor arguments passed in. Default the values
            if self.IsFutures:
                self.HedgeNotional = 100000  # defaults to 100,000 for Futures contracts
            else:
                self.HedgeNotional = 1
            self.HedgeCost = 0
            self.Beta = 1.0
            self.Side = TradeSide.Ask # default to Ask

    def __calculate_hedge_contracts(self):
        if self.TradeObj.Side == TradeSide.Ask:
            self.Side = TradeSide.Bid
        else:
            self.Side = TradeSide.Ask

        if self.TradeObj.DV01 > self.MinHedgeDV01:
            if self.IsFutures:
                self.HedgeContracts = np.round(self.Beta * self.TradeObj.DV01 / self.DV01,0)
            else:
                self.HedgeContracts = self.Beta * self.TradeObj.DV01 / self.DV01
        else:
            self.HedgeContracts = 0.0

    def calculate_initial_hedge_cost(self, contracts = None):
        if contracts is None:
            self.__calculate_hedge_contracts()
        else:
            self.HedgeContracts = contracts
        if self.HedgeContracts > 0:
            # Changed: 16th Feb, 2017 - Initial Hedge cost is just the # of contracts
            self.HedgeCost = self.HedgeContracts * self.HedgeNotional
            # if self.Side == TradeSide.Ask:
            #     self.HedgeCost = self.BidPx * self.HedgeContracts * self.HedgeNotional/100
            # else:
            #     self.HedgeCost = self.AskPx * self.HedgeContracts * self.HedgeNotional / 100
        else:
            self.HedgeCost = 0.0

    # def __str__(self):
    #     return "Hedge: Sym = %s, MidPx = %s, Beta = %s, DV01 = %s, HedgeContracts = %s, HedgeCost = %s" % \
    #            (self.Sym, self.MidPx, self.Beta, self.DV01, self.HedgeContracts, self.HedgeCost)


if __name__ == '__main__':
    tr = trade.Trade()
    tr.TradeId = '111'
    tr.Sym = '9128235'
    tr.Notional = 10*1e6
    tr.Side = TradeSide.Bid
    tr.TradedPx = 96.916
    tr.MidPx = 96.928
    tr.ClientSysKey = 111
    tr.Duration = 18.67
    tr.ONRepo = 0.02
    tr.TradeDate = dt.datetime(2017,2,14)
    tr.Ccy = 'EUR'
    tr.calculate_trade_dv01()
    # arg = ['GT30', 'GT30', 99, 99, 99, 1.0, 21, 1000, False, 1.0, 1, [99, 99.01, 99.02, 99.03, 99.05], False]

    hedge = Hedge()
    hedge.AskPx = 110.2095
    hedge.MidPx = 110.205
    hedge.BidPx = 110.2000
    hedge.DV01 = 94.65
    hedge.Beta = 0.85
    hedge.IsFutures = True
    hedge.TradeObj = tr
    hedge.HedgeNotional = 100000
    hedge.Sym = tr.Sym
    # hedge.calculate_initial_hedge_cost()
    print(hedge)
