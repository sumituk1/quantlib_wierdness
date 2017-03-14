import random

from core.hedge import *
from core.trade import *

# from markout import *
from core.riskpath import *
from core.riskpath_status import *


class ClientPnl:
    # Attributes
    ClientPnlId = str(random.getrandbits(32))
    RiskPathId = None
    ClientSysKey = None
    TradedPx = None
    MidPx = None
    AskPx = None
    BidPx = None
    Side = TradeSide.Bid
    Notional = None
    DV01 = None
    UPnl = None
    HPnl = None
    RiskRedn = False
    RiskRednUsed = False
    TradeObj = None
    HedgeArr = []
    RiskPathClosureTol = 0.0
    ForceClose = False
    CouponRecToday = False # <-- used for adding coupon cashflows for P&L
    CouponCF = 0.0

    def __init__(self, timestamp, rp_id, tr):
        self.ClientPnlId = str(random.getrandbits(32)) + "_" + timestamp.date().strftime("%Y%m%d")
        self.RiskPathId = rp_id
        self.Side = tr.side
        self.TradeObj = tr # stores the Trade object
        self.ClientSysKey = tr.client_key
        self.TradedPx = tr.traded_px
        self.MidPx = tr.mid_px
        self.UPnl = None  # We will calculate this
        self.HedgeArr = []
        # self.HPnl = None

    # % -----------------------------------------------------------------------------------------
    # % calculate client Pnl based on:
    # % 1. current trade
    # % 2. hedge array
    # % 3. openRiskPath
    # % -----------------------------------------------------------------------------------------
    def calculateClientPnl(self, rp, tr, h_arr):
        # % Check if this is a RiskReduction Client trade
        if tr.side == TradeSide.Bid:
            if not rp.Status == RiskPathStatus.ForceClose:
                self.UPnl = (+tr.mid_px - tr.traded_px) * tr.notional / 100
            # else:
            #     # This trade is a d2d and is forclosing the RiskPath
            #     self.UPnl = (-tr.MidPx + tr.BidPx) * tr.Notional / 100
        else:  # Side = Ask
            if not rp.Status == RiskPathStatus.ForceClose:
                self.UPnl = (-tr.mid_px + tr.traded_px) * tr.notional / 100
            # else:
            #     # This trade is a d2d and is forclosing the RiskPath
            #     self.UPnl = (+tr.MidPx - tr.AskPx) * tr.Notional / 100

        # % Check if its a risk - reduction trade
        if tr.side != rp.Side:
            # % risk - reduction
            self.RiskRedn = True
        else:
            # % risk add - on
            self.RiskRedn = False

        # % Set the clientPnl Notional based on RiskPathClosureTolerance
        self.calculateClientPnlNotional(tr, rp)

        # % First add the hedge to the HedgeArray
        if not h_arr is None:
            if not self.TradeObj.is_benchmark:
                for i in range(len(h_arr)):
                    # % 1.Add this NEW hedge to the clientPnlArr
                    self.addHedgeToArr(h_arr[i])
                # % Always calculate hedge Pnl.
                for i in range(len(self.HedgeArr)):
                    if not self.HedgeArr[i] is None:
                        if self.HedgeArr[i].Side == TradeSide.Bid:  # Trade side is Bid. So sell the hedge
                            # Buying the hedge at AskPx
                            if not self.HPnl is None:
                                self.HPnl += (-self.HedgeArr[i].AskPx + self.HedgeArr[i].MidPx) * self.HedgeArr[i].HedgeCost / 100
                            else:
                                self.HPnl = (-self.HedgeArr[i].AskPx + self.HedgeArr[i].MidPx) * self.HedgeArr[i].HedgeCost / 100
                        else:
                            # Selling the hedge at BidPx
                            if not self.HPnl is None:
                                self.HPnl += (self.HedgeArr[i].BidPx - self.HedgeArr[i].MidPx) * self.HedgeArr[i].HedgeCost / 100
                            else:
                                self.HPnl = (self.HedgeArr[i].BidPx - self.HedgeArr[i].MidPx) * self.HedgeArr[i].HedgeCost / 100

                        # self.HPnl = self.HPnl + self.HedgeArr[i].HedgeCost
            else:
                # This is a benchmark bond. So no hedging? todo: Check!!
                if tr.Side == TradeSide.Bid:  # Trade side is Bid.So sell the hedge
                    self.HPnl = (tr.BidPx - tr.MidPx) * tr.Notional / 100
                else:
                    self.HPnl = (-tr.AskPx + tr.MidPx) * tr.Notional / 100

    # % -----------------------------------------------------------------------------------------
    # % Adds a clientPnl object to the ClientPnlArr for a given RiskPath
    # % -----------------------------------------------------------------------------------------
    def addHedgeToArr(self, h):
        # This is typically needed for a RR trade Split.
        # The underlying TradeObj in Hedge needs to be updated
        h.TradeObj = self.TradeObj
        h.RiskPathId = self.RiskPathId
        # Now make sure the HedgeCost is updated
        h.calculate_initial_hedge_cost()

        # Set the Side of the Hedge correctly.
        if self.Side == TradeSide.Ask:
            h.Side = TradeSide.Bid
        self.HedgeArr.append(h)

    # % -----------------------------------------------------------------------------------------
    # % Check the tolerance of Notional to be allocated to clientPnl function
    # % -----------------------------------------------------------------------------------------
    def calculateClientPnlNotional(self, tr, rp):
        minNotional = rp.Notional * (1 - self.RiskPathClosureTol)
        maxNotional = rp.Notional * (1 + self.RiskPathClosureTol)

        # % First default the notional to the trade notional.
        self.Notional = tr.notional

        if self.RiskRedn and (self.RiskPathClosureTol > 0.0):
            if maxNotional >= tr.notional >= minNotional:
                self.Notional = rp.Notional
