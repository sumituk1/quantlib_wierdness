import copy
import datetime as dt

from core.client_pnl import *
from core.trade import *

from quantlib.bond.fixed_bond import *
from common.read_config import *
from core.riskpath_status import *


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class RiskPath:
    # Attributes
    RiskPathId = str(random.getrandbits(32))
    InitiationDate = None  # RiskPath initiation date
    InitiationTime = None  # RiskPath initiation time
    ClosureDate = None
    ClosureTime = None
    # StartDate = None # ??
    LastUpdatedTimestamp = None  # updated date
    # TradeId = None
    Sym = None  # CUSIP/Sym
    Notional = None  # Outstanding Notional on the RiskPath
    Side = TradeSide.Bid  # Side of RiskPath
    HolidayCentre = "EUR"
    ClientPnlArr = []  # Array of ClientPnl
    # TradedPx = None
    # MidPx = None
    # BidPx = None
    # AskPx = None
    # Duration = None
    ONRepo = float(get_data_given_section_and_key("Rates-RiskPath", "ONRepo"))  # ON repo used to roll over RiskPath
    bIncludeCostOfCarry = str2bool(get_data_given_section_and_key("Rates-RiskPath", "IncludeCostOfCarry"))
    IsD2dForceClose = False  # Is the RP force closed?
    Status = RiskPathStatus.Open
    DaysForceClose = int(get_data_given_section_and_key("Rates-RiskPath", "DaysForceClose"))
    RiskPathClosureTol = float(get_data_given_section_and_key("Rates-RiskPath", "RiskPathClosureTol"))

    # TradeAddedToRP = False
    Rc = None
    Sales = None

    # Trader = None

    # Constructor for RiskPath
    def __init__(self, timestamp, sym, side, notional=None, bIncludeCostOfCarry=None):
        # Mandatory arguments for constructing a new RiskPath
        self.RiskPathId = str(random.getrandbits(32)) + "_" + timestamp.date().strftime("%Y%m%d")
        self.InitiationDate = timestamp.date()
        self.InitiationTime = timestamp.time()
        self.LastUpdatedTimestamp = timestamp
        self.Sym = sym
        self.Side = side
        self.Notional = notional
        self.ClientPnlArr = []  # Array of ClientPnl
        self.ClosureDate = None
        self.ClosureTime = None
        self.IsD2dForceClose = False  # Is the RP force closed?
        self.__setRPStatus(timestamp, RiskPathStatus.Open)
        if not bIncludeCostOfCarry is None:
            self.bIncludeCostOfCarry = bIncludeCostOfCarry

    # *** Creates a new RiskPath and allocates Trades and hedges to ClientPnl Array
    @staticmethod
    def create_new(trade,
                   hedge,
                   timestamp,
                   holidayCentre,
                   bIncludeCostOfCarry):

        # Create a new RiskPath from a arrival of a trade
        rp = RiskPath(timestamp, trade.Sym, trade.Side, tr.Notional)
        rp.HolidayCentre = holidayCentre
        rp.IncludeCostOfCarry = bIncludeCostOfCarry

        # ** now add this trade and hedge(via the clientPnl) to this newly created RiskPath
        rp = RiskPath.update(rp, trade, hedge)

        return rp

    # @staticmethod

    # % -----------------------------------------------------------------------------------------
    # *** Updates the clientPnlArray by adding / amending the clientPnlArray for a RiskPath
    # % -----------------------------------------------------------------------------------------
    def update(self, timestamp, trade, hedge_arr=None, closeHedgePxArr=None): #*args):  # trade, hedge):
        if self.Status == RiskPathStatus.Close:
            msg = '[RiskPath:update] Update called on closed RiskPath.'
            raise ValueError(msg)
            # return
        bAdjustHedgesForRiskRedn = False
        if trade.trade_id.find('HYPOTHETICAL') != -1:
            bForceCloseRP = True
        else:
            bForceCloseRP = False
        # hedge_arr = []
        # hedgeClosePxArr = []
        # check input args
        # if len(args) == 0:
        #     bForceCloseRP = True  # if no arguments passed in- it's assumed this update() call is to check for forceClose ONLY
        # elif len(args) == 2:  # only trade with no hedges
        #     # ts = args[0]  # timestamp
        #     # trade = args[1]  # trade
        #     if trade.TradeId.find('HYPOTHETICAL') != -1:
        #         bForceCloseRP = True
        # elif len(args) == 3:  # 1 hedge
        #     # ts = args[0]  # timestamp
        #     # trade = args[1]
        #     hedge_arr = args[2]
        # elif len(args) == 4:  # <-- closing Hedge Prixes bid/ask array
        #     ts = args[0]  # timestamp
        #     trade = args[1]
        #     if trade.TradeId.find('HYPOTHETICAL') != -1:
        #         bForceCloseRP = True
        #     hedge_arr = args[2]
        #     hedgeClosePxArr = args[3]
        # else:
        #     ts = args[0]  # timestamp
        #     trade = args[0]
        #     if trade.TradeId.find('HYPOTHETICAL') != -1:
        #         bForceCloseRP = True
        #     for i in range(1, len(args)):
        #         hedge_arr.append(args[i])

        # % 1. Create a ClientPnl object
        bStartNewRP, tr_new_RP, tr_add_to_RP, bSplitRRTrade = self.__checkAndSplitRRTrade(trade)
        clientPnl = ClientPnl(timestamp, self.RiskPathId, tr_add_to_RP)
        clientPnl.RiskPathClosureTol = self.RiskPathClosureTol
        # clientPnl.calculateClientPnl(self, tr_add_to_RP, hedge_arr)
        #
        # # clientPnl.UPnl = None  # for Credit, set the UPnl to NaN at point of trade.We will update this when we do COB P & L
        # # % [bClientPnlArrExists, ~, ~] = checkClientPnlArrExists(obj, clientPnl);
        #
        # # % 1. Add this NEW client to the clientPnlArr
        # #  %   Also - adjusts the overall RiskPath Notional
        # pos = self.__addClientPnl(clientPnl)

        # %%% 3. Allocate riskreduction to the existing clientPnlArray in a RiskPath
        if not clientPnl.Side == self.Side:  # % This is a risk reduction trade and has not been processed before
            # No hedge_array for risk_redn trade. We will re-allocate/unwind the hedges as a result
            # of this RR trade taking us out of Risk
            clientPnl.calculateClientPnl(self, tr_add_to_RP,h_arr=None)
            pos = self.__addClientPnl(clientPnl)

            self.__allocateFIFORiskRednNotional(clientPnl, pos, closeHedgePxArr)
            bAdjustHedgesForRiskRedn = True
            # todo: the below is for Credit
            # trade.Notional = riskRednClientPnl.Notional ?? # ; % for a risk - reduction trade, adjust the input trade notional.
            # if bStartNewRP:
            #     # % Remove this trade from the ClientPnlArray of this RP
            #     del self.ClientPnlArr[pos]
        else:
            # Not a RiskRedn trade. Add all the hedges if the hedge_arr is passed in
            # Make sure the side of the hedges are opposite to the Trade
            clientPnl.calculateClientPnl(self, tr_add_to_RP, h_arr=hedge_arr)
            pos = self.__addClientPnl(clientPnl)
            tr_add_to_RP.TradeAddedToRP = True  # % if same side as a open RP, then trade has been successfully added to a open RP.

        # Check if this is a call to ForceCLose the RP. Unwind the hedges appropriately
        if bForceCloseRP and not closeHedgePxArr is None:
            # unwind the hedges
            self.__unwindHedges(closeHedgePxArr)

        # Check if this is a call to adjust the open RP for a risk Redn trade. Unwind/adjust the hedges appropriately
        # if bAdjustHedgesForRiskRedn and not hedgeClosePxArr is None:
        #     # unwind the hedges
        #     self.__adjustHedgesDueToRiskRedn(timestamp,clientPnl,hedgeClosePxArr)

        # % Check if RiskPath needs to close down.
        if self.Notional == 0.0:
            self.__setRPStatus(timestamp, RiskPathStatus.Close)

        # Finally return the flag to either create a new RP based on splitting of RR trade
        return bStartNewRP, tr_new_RP, bSplitRRTrade

    # % -----------------------------------------------------------------------------------------
    # *** Checks if RiskPath duration > DaysToForceClose. If greater, then sets the ForceClose status = TRUE.
    # *** Else - calculates the mid - to - mid Pnl function
    # % -----------------------------------------------------------------------------------------
    def rolloverRiskPath(self, timestamp, tradeMidPx_t, hedgePxArr=None, prevCloseDate=None):
        if self.Status == RiskPathStatus.Close:
            msg = '[RiskPath:rolloverRiskPath] Rollover called on closed RiskPath.'
            raise ValueError(msg)
            # return

        if self.Notional > 0:
            # TODO:%Calculate the Mid-to-Mid markout for hedges
            self.__calculateRolloverMid2MidMarkouts(timestamp, tradeMidPx_t, hedgePxArr, prevCloseDate)

        # Check if the RP Status should be set to ForceClose.
        # This will be actioned upon in __forceCloseRiskPathWithD2D()
        dateDiff = self.LastUpdatedTimestamp.date() - self.InitiationDate
        if dateDiff.days >= self.DaysForceClose:
            self.__setRPStatus(timestamp, RiskPathStatus.ForceClose)

    # Private method
    # % -----------------------------------------------------------------------------------------
    # *** Updates the hedge contracts by either partially closing out position or unwinding the
    #     entire hedge
    # % -----------------------------------------------------------------------------------------
    # def __adjustHedgesDueToRiskRedn(self, timestamp, riskRedTrade, hedgeClosePxArr):


    # % -----------------------------------------------------------------------------------------
    # *** Unwinds all the hedges given the close Hedge bid/ask Prices
    # % -----------------------------------------------------------------------------------------
    def __unwindHedges(self,hedgeClosePxArr):
        for i in range(0,len(self.ClientPnlArr)):
            self.ClientPnlArr[i] = self.__calculateHedgePnl(self.ClientPnlArr[i],
                                                            hedgeClosePxArr,
                                                            bUnwindHedges = True)

    # % -----------------------------------------------------------------------------------------
    # *** Checks if the close-out client Trade is > the outstanding RP Notional.
    # *** If it is, then splits the client trade into 2. First one closes out the currenr RP
    # and the remaining is to start a new RP.
    # % -----------------------------------------------------------------------------------------
    def __checkAndSplitRRTrade(self, trade):
        minNotional = self.Notional * (1 - self.RiskPathClosureTol)
        maxNotional = self.Notional * (1 + self.RiskPathClosureTol)
        bSplitRRTrade = False
        if (self.Notional > 0) and (self.Status == RiskPathStatus.Open):
            if trade.notional > maxNotional and trade.side != self.Side:
                # Split the trade and start a new RP
                bSplitRRTrade = True
                tr_new_RP = copy.deepcopy(trade)  # do a deep copy of the existing trade object
                tr_new_RP.notional = trade.notional - self.Notional  # Reset the newly created TradeNotional
                tr_new_RP.calculate_trade_dv01()
                tr_add_to_RP = copy.deepcopy(trade)
                tr_add_to_RP.notional = self.Notional  # Reset the newly created TradeNotional
                return True, tr_new_RP, tr_add_to_RP,bSplitRRTrade

        return False, None, trade,bSplitRRTrade

    def __calculateRolloverMid2MidMarkouts(self, timestamp, tradeMidPx_t, hedgePxArr=None, prevCloseDate=None):
        bDoPricePnl = True
        for i in range(len(self.ClientPnlArr)):
            if not self.ClientPnlArr[i].RiskRedn:  # %Update the Mid-to-mid markout only if this is not a risk-reduction trade
                # m2mIndex = len(self.ClientPnlArr) - 1
                # todo: Add cost of carry
                if self.bIncludeCostOfCarry:
                    if not prevCloseDate is None:
                        self.__calculateCostOfCarry(timestamp, self.ClientPnlArr[i], tradeMidPx_t, prevCloseDate)
                        bDoPricePnl = False

                if bDoPricePnl:
                    # No cost-of-carry calculation. Only Price movement
                    if self.ClientPnlArr[i].Side == TradeSide.Bid:
                        if self.ClientPnlArr[i].UPnl is None:
                            self.ClientPnlArr[i].UPnl = (-self.ClientPnlArr[i].MidPx + tradeMidPx_t) * \
                                                        self.ClientPnlArr[i].Notional / 100
                        else:
                            self.ClientPnlArr[i].UPnl += (-self.ClientPnlArr[i].MidPx + tradeMidPx_t) * \
                                                         self.ClientPnlArr[i].Notional / 100
                    else:
                        if self.ClientPnlArr[i].UPnl is None:
                            self.ClientPnlArr[i].UPnl = (self.ClientPnlArr[i].MidPx - tradeMidPx_t) * \
                                                        self.ClientPnlArr[i].Notional / 100
                        else:
                            self.ClientPnlArr[i].UPnl += (self.ClientPnlArr[i].MidPx - tradeMidPx_t) * \
                                                         self.ClientPnlArr[i].Notional / 100

                # todo: Calculate the Hedge markout for all ClientPnls
                self.ClientPnlArr[i] = self.__calculateHedgePnl(self.ClientPnlArr[i], hedgePxArr)

                self.ClientPnlArr[i].MidPx = tradeMidPx_t  # %Reset the tradeMidPx for later Mid2Mid markout

    # %*******************************************************************
    # % Calculates the hedge P&L for the corresponding client /d2d trade
    # % Note that the hedge can be a collection of different hedges
    #   THIS IS ALWAYS for ROLLOVER
    # %*******************************************************************
    def __calculateHedgePnl(self, clientPnl, hedgePxArr, bUnwindHedges = False):
        # if nargin <= 4
        #    bRollOverMtm = false;
        # end
        #
        # hPnl = 0;
        #
        if clientPnl.Notional > 0:
            clientPnl.HPnl = None

        if not clientPnl.RiskRedn and clientPnl.Notional > 0.0:
            if bUnwindHedges:
                clientPnl.HPnl = None
                # unwind the hedges. Typically this is a ForceClose
                for i in range(0, len(clientPnl.HedgeArr)):
                    if clientPnl.HedgeArr[i].Side == TradeSide.Bid:  # Hedge is a Buy
                        if not clientPnl.HPnl is None:
                            clientPnl.HPnl += (-clientPnl.HedgeArr[i].AskPx + hedgePxArr[i, 0]) * \
                                             clientPnl.HedgeArr[i].HedgeCost / 100  # <-- 0 is Bid, 1 = Ask
                        else:
                            clientPnl.HPnl = (-clientPnl.HedgeArr[i].AskPx + hedgePxArr[i,0]) * \
                                              clientPnl.HedgeArr[i].HedgeCost / 100             #<-- 0 is Bid, 1 = Ask
                    else:
                        if not clientPnl.HPnl is None:
                            clientPnl.HPnl += (clientPnl.HedgeArr[i].BidPx - hedgePxArr[i, 1]) * \
                                             clientPnl.HedgeArr[i].HedgeCost / 100
                        else:
                            clientPnl.HPnl = (clientPnl.HedgeArr[i].BidPx - hedgePxArr[i,1]) * \
                                             clientPnl.HedgeArr[i].HedgeCost / 100
                    # Hedge has been unwound
                    clientPnl.HedgeArr[i].TradeObj.notional = 0.0
                    clientPnl.HedgeArr[i].TradeObj.calculate_trade_dv01()
                    # Always recompute the hedge cost once the contracts have been reset
                    clientPnl.HedgeArr[i].calculate_initial_hedge_cost()
            else:
                # do mid-to-mid Hedge P&L
                for i in range(0, len(clientPnl.HedgeArr)):
                    # %for each hedge for a client trade, perform the mid-to-mid calculation
                    if not clientPnl.RiskRedn:  # skip for riskredn trade
                        if clientPnl.HedgeArr[i].Side == TradeSide.Bid:  # Hedge is a Buy
                            # Buying the hedge at AskPx
                            if not clientPnl.HPnl is None:
                                # Note: the below is done because a single trade/clientPnl might have multiple hedges
                                clientPnl.HPnl += (-clientPnl.HedgeArr[i].AskPx + np.average(hedgePxArr[i])) * \
                                                  clientPnl.HedgeArr[i].HedgeCost / 100
                            else:
                                clientPnl.HPnl = (-clientPnl.HedgeArr[i].AskPx + np.average(hedgePxArr[i])) * \
                                                 clientPnl.HedgeArr[i].HedgeCost / 100
                        else:
                            # Hedge is a Sell
                            if not clientPnl.HPnl is None:
                                clientPnl.HPnl += (clientPnl.HedgeArr[i].BidPx - np.average(hedgePxArr[i])) * \
                                                  clientPnl.HedgeArr[i].HedgeCost / 100
                            else:
                                clientPnl.HPnl = (clientPnl.HedgeArr[i].BidPx - np.average(hedgePxArr[i])) * \
                                                 clientPnl.HedgeArr[i].HedgeCost / 100

                            clientPnl.HedgeArr[i].MidPx = np.average(hedgePxArr[i])

        return clientPnl

    # % -----------------------------------------------------------------------------------------
    # ** Force closes a open RiskPath if the RiskPath has been open beyond a threshold
    # % -----------------------------------------------------------------------------------------
    def __forceCloseRiskPathWithD2D(self, timestamp, notional, askPx, midPx, bidPx, closeHedgePxArr=None):
        if self.Status == RiskPathStatus.Close:
            msg = 'RiskPath:forceCLoseRiskPathWithD2D-forceCLoseRiskPathWithD2D called on closed RiskPath.'
            raise ValueError(msg)

        d2dTrade = FixedIncomeTrade()
        d2dTrade.trade_id = 'HYPOTHETICAL BROKER TRADE'
        d2dTrade.sym = self.Sym
        d2dTrade.notional = notional
        if self.Side == TradeSide.Bid:
            d2dTrade.side = TradeSide.Ask  # %1=Bid
        else:
            d2dTrade.side = TradeSide.Bid  # %1=Bid

        d2dTrade.traded_px = None
        d2dTrade.mid_px = midPx  # % Use TWeb mid
        d2dTrade.bid_px = bidPx  # % Use TWeb bid
        d2dTrade.ask_px = askPx  # % Use TWeb ask
        d2dTrade.client_key = 100  # %Reserve 100 as the d2d client syskey
        d2dTrade.duration = 0.0  # %Not yet required for Credit Cash
        d2dTrade.is_d2d_force_close = True
        d2dTrade.trade_date = self.ClosureDate

        # %Add this D2D client Pnl to the RiskPath object
        self.IsD2dForceClose = True
        self.update(timestamp=timestamp, trade=d2dTrade, closeHedgePxArr=closeHedgePxArr)
        self.__setRPStatus(timestamp, RiskPathStatus.ForceClose)

    # % -----------------------------------------------------------------------------------------
    # % Calculates the hedge P & L for the corresponding client / d2d trade
    # % Note that the hedge can be a collection of different hedges
    # % -----------------------------------------------------------------------------------------
    # def calculateHedgePnl(self, clientIndex, m2mIndex, bRollOverMtm, hedgePxArr)


    # % -----------------------------------------------------------------------------------------
    # ** Adds a clientPnl object to the ClientPnlArr for a given RiskPath
    # % -----------------------------------------------------------------------------------------
    def __addClientPnl(self, clientPnl, bInitRiskPath=False):
        self.ClientPnlArr.append(clientPnl)
        pos = len(self.ClientPnlArr)  # % are there any existing clientPnl objects?

        if not pos == 1:
            if clientPnl.Side != self.Side:
                self.Notional = max(0, self.Notional - clientPnl.Notional)  # %Risk reduction
            else:
                self.Notional = self.Notional + clientPnl.Notional  # %Risk add-on
                # elif (clientPnl.TradeObj.RiskFlag == RiskFlag.Risk)
                #     if clientPnl.Side ~= obj.Side
                #         obj.Notional = max(0,obj.Notional - clientPnl.Notional); %Risk reduction
                #     else
                #         obj.Notional = obj.Notional + clientPnl.Notional; %Risk add-on
                #     end
        return pos

        # % -----------------------------------------------------------------------------------------
        # % Called from rolloverRiskPath. Used to calculate the Mid2Mid markout for a rollover date
        # % -----------------------------------------------------------------------------------------
        # def __calculateRolloverMid2MidMarkouts(self, tradeMidPx, prevDate, hedgePxArr):
        # for i in range(len(self.ClientPnlArr)):
        #     if not self.ClientPnlArr[i].RiskRedn: # Update the Mid-to-mid markout only if this is not a risk-reduction trade
        #         m2mIndex = len(seld.ClientPnlArr) # % j is the counter of the current index in the RiskPath. Used only for Mid-to-mid markouts
        #         if self.IncludeCostOfCarry:
        #                             self.ClientPnlArr[i].UPnl +=  self.__calculateRolloverMid2MidMarkouts(self.ClientPnlArr[m2mIndex].MidPx, tradeMidPx,prevDate, obj.CurrentDate,obj.ClientPnlArr(i).TradeObj.ONRepo,obj.ClientPnlArr(i).Notional,obj.ClientPnlArr(i).Side)
        #

    # % -----------------------------------------------------------------------------------------
    # ** Allocates a Risk Redn trade on a FIFO basis
    # % -----------------------------------------------------------------------------------------
    def __allocateFIFORiskRednNotional(self, riskRednClientPnl, riskRednPos, hedgeClosePxArr=None):

        for i in range(len(self.ClientPnlArr)):  # % last element is the new item added
            if (not self.ClientPnlArr[i].RiskRedn) and (self.ClientPnlArr[i].Notional > 0) and (
                    not riskRednClientPnl.RiskRednUsed):

                # First check if this is a Hypothetical D2d force-closing the RiskPaths
                if (riskRednClientPnl.UPnl is None) and ("HYPOTHETICAL" in riskRednClientPnl.TradeObj.trade_id):

                    if self.ClientPnlArr[i].Side == TradeSide.Bid:
                        self.ClientPnlArr[i].UPnl += (-self.ClientPnlArr[i].MidPx + riskRednClientPnl.TradeObj.bid_px) * \
                                                     self.ClientPnlArr[i].Notional / 100
                    else:
                        self.ClientPnlArr[i].UPnl += (self.ClientPnlArr[i].MidPx - riskRednClientPnl.TradeObj.ask_px) * \
                                                     self.ClientPnlArr[i].Notional / 100

                    # Hypothetical broker/ D2D trades will ALWAYS close down a full ClientPnl
                    riskRednClientPnl.Notional -= self.ClientPnlArr[i].Notional

                    # Unwind the hedges before closing out the clientPnl
                    self.__calculateHedgePnl(self.ClientPnlArr[i],hedgePxArr=hedgeClosePxArr,bUnwindHedges=True)
                    self.ClientPnlArr[i].Notional = 0
                    # self.Notional -= riskRednClientPnl.Notional # reduce the overall outstanding Notional of the RiskPath
                else:
                    # Not a d2d force close. Now check for client flows de-risking the RiskPaths
                    if riskRednClientPnl.Notional < self.ClientPnlArr[i].Notional:
                        # %** 20th Nov, 2015 - Check if the RiskReduction UPnl is -ve. Re-distribute this Pnl accordingly to
                        # %risk-add on trades that it's taking out of Risk.
                        if riskRednClientPnl.UPnl < 0:
                            redistribPnl = riskRednClientPnl.UPnl
                            riskRednClientPnl.UPnl = riskRednClientPnl.UPnl - redistribPnl
                            self.ClientPnlArr[riskRednPos - 1].UPnl = riskRednClientPnl.UPnl
                            self.ClientPnlArr[i].UPnl = self.ClientPnlArr[i].UPnl + redistribPnl

                        # %Partially closing down a ClientPnl object in a RiskPath
                        self.ClientPnlArr[i].Notional -= riskRednClientPnl.Notional
                        self.ClientPnlArr[riskRednPos - 1].RiskRednUsed = True  # %If the RiskRedn is fully used, then reset the flag
                        riskRednClientPnl.RiskRednUsed = True
                        riskRednClientPnl.Notional = 0

                        # %TODO: Reduce the number of hedge contracts and modify the hedgeCost
                        # 1. Split the hedge into close-out and open contracts
                        # 2. Do a close-out HPnl of the close-out contracts
                        # 3. Then do a Mid P&L of the open contracts

                        for k in range(len(self.ClientPnlArr[i].HedgeArr)):
                            # store the original hedge contracts before modifications
                            orig_hedge_contracts = self.ClientPnlArr[i].HedgeArr[k].HedgeContracts
                            # set the notional correctly on the underlying trade object and reset the DV01 of the trade
                            self.ClientPnlArr[i].HedgeArr[k].TradeObj.notional = self.ClientPnlArr[i].Notional
                            self.ClientPnlArr[i].HedgeArr[k].TradeObj.calculate_trade_dv01()
                            # adjust the number of hedge contracts to hedge the outstanding duration risk of trade
                            self.ClientPnlArr[i].HedgeArr[k].calculate_initial_hedge_cost()
                            open_hedge_contracts = self.ClientPnlArr[i].HedgeArr[k].HedgeContracts
                            open_hedge_cost =  self.ClientPnlArr[i].HedgeArr[k].HedgeCost

                            # for the unwound contracts, compute the cost of unwinding
                            contracts_to_unwind = max(orig_hedge_contracts -
                                                      self.ClientPnlArr[i].HedgeArr[k].HedgeContracts,0)
                            self.ClientPnlArr[i].HedgeArr[k].calculate_initial_hedge_cost(contracts_to_unwind)
                            close_hedge_cost = self.ClientPnlArr[i].HedgeArr[k].HedgeCost

                            # first close out the # hedge contracts based on risk-off from the riskredn trade
                            if self.ClientPnlArr[i].HedgeArr[k].Side == TradeSide.Ask:
                                # Close out open hedge at Ask
                                x = close_hedge_cost * \
                                    (-hedgeClosePxArr[k,1] + self.ClientPnlArr[i].HedgeArr[k].BidPx)/100
                            else:
                                # Close out open hedge at Bid
                                x = close_hedge_cost * \
                                    (+hedgeClosePxArr[k, 0] - self.ClientPnlArr[i].HedgeArr[k].AskPx) / 100
                            if k == 0:
                                self.ClientPnlArr[i].HPnl = x
                            else:
                                self.ClientPnlArr[i].HPnl += x

                            # Now do a P&L of the "open" contracts
                            self.ClientPnlArr[i].HedgeArr[k].calculate_initial_hedge_cost(open_hedge_contracts)
                            if self.ClientPnlArr[i].HedgeArr[k].Side == TradeSide.Ask:
                                # Close out open hedge at Ask
                                self.ClientPnlArr[i].HPnl += open_hedge_cost * \
                                    (-np.average(hedgeClosePxArr[k, :]) + self.ClientPnlArr[i].HedgeArr[k].BidPx) / 100
                            else:
                                # Close out open hedge at Bid
                                self.ClientPnlArr[i].HPnl += open_hedge_cost * \
                                    (+np.average(hedgeClosePxArr[k, :]) - self.ClientPnlArr[i].HedgeArr[k].AskPx) / 100

                            # # %======================================================================
                            # # %Since this riskredn trade is used up
                            # # %completely to close down a ClientPnl, the
                            # # %left over contracts & hedge cost will be 0
                            # # %after allocation.
                            # # %======================================================================
                            # self.ClientPnlArr[riskRednPos].HPnl = self.ClientPnlArr[riskRednPos].HPnl - \
                            #                                       riskRednClientPnl.HedgeArr[
                            #                                           k].HedgeCost  # %Reduce the total hedge cost after allocation to other client trades
                            # self.ClientPnlArr[riskRednPos].HedgeArr[k].HedgeCost = 0.0
                            # self.ClientPnlArr[riskRednPos].HedgeArr[k].HedgeContracts = 0.0
                            #
                            # riskRednClientPnl.HPnl = riskRednClientPnl.HPnl - riskRednClientPnl.HedgeArr[k].HedgeCost
                            # riskRednClientPnl.HedgeArr[k].HedgeContracts = 0
                            # riskRednClientPnl.HedgeArr[k].HedgeCost = 0.0
                    else:
                        # %This is closing down a ClientPnl object in a  RiskPath
                        # %** 20th Nov, 2015 - Check if the RiskReduction UPnl is -ve. Re-distribute this Pnl accordingly to
                        # %risk-add on trades that it's taking out of Risk.
                        if riskRednClientPnl.UPnl < 0:
                            redistribPnl = riskRednClientPnl.UPnl * self.ClientPnlArr[
                                i].Notional / riskRednClientPnl.Notional
                            riskRednClientPnl.UPnl -= redistribPnl
                            self.ClientPnlArr[riskRednPos - 1].UPnl = riskRednClientPnl.UPnl
                            self.ClientPnlArr[i].UPnl += redistribPnl

                        # Before closing out the ClientPnl on this RP, do a Pnl on it
                        self.ClientPnlArr[i].UPnl += self.calculateClientPnlOnCloseRP(self.ClientPnlArr[i],
                                                                                      riskRednClientPnl.TradedPx)
                        # Reduce the outstanding amount on the riskReducing ClientPnl
                        riskRednClientPnl.Notional = riskRednClientPnl.Notional - self.ClientPnlArr[i].Notional

                        # %todo:***Calculate the re-distribution of hedge cost to this client trade
                        self.ClientPnlArr[i] = self.__calculateHedgePnl(self.ClientPnlArr[i],
                                                                        hedgeClosePxArr,
                                                                        bUnwindHedges=True)
                        # Set the clientPnl in RP to 0
                        self.ClientPnlArr[i].Notional = 0
                        # for k in range(len(self.ClientPnlArr[i].HedgeArr)):
                        #     redistributedHedgeCost = riskRednClientPnl.HedgeArr[k].HedgeCost * \
                        #                              self.ClientPnlArr[i].HedgeArr[k].HedgeContracts / \
                        #                              riskRednClientPnl.HedgeArr[k].HedgeContracts
                        #
                        #     self.ClientPnlArr[i].HPnl = self.ClientPnlArr[i].HPnl + redistributedHedgeCost
                        #     # %** Reduce the hedge cost,HPnl of the risk-reduction trade as it's redistributed
                        #     # %======================================================================
                        #     # %Since this riskredn trade is partially used up to close down ClientPnl, the
                        #     # %left over contracts & hedge cost will now be
                        #     # %reset both in the RP array and the individual
                        #     # %RiskRedn object after allocation.
                        #     # %======================================================================
                        #     # % riskRednClientPnl.HedgeArr(k).HedgeCost = riskRednClientPnl.HedgeArr(k).HedgeCost - redistributedHedgeCost;
                        #     # % riskRednClientPnl.HPnl = riskRednClientPnl.HPnl - redistributedHedgeCost;
                        #
                        #     # %Reduce the hedge contracts
                        #     self.ClientPnlArr[riskRednPos].HPnl = \
                        #         self.ClientPnlArr[
                        #             riskRednPos].HPnl - redistributedHedgeCost  # '%Reduce the total hedge cost after allocation to other client trades
                        #     self.ClientPnlArr[riskRednPos].HedgeArr[k].HedgeCost = \
                        #         self.ClientPnlArr[riskRednPos].HedgeArr[k].HedgeCost - redistributedHedgeCost
                        #     self.ClientPnlArr[riskRednPos].HedgeArr[k].HedgeContracts = \
                        #         max(0, self.ClientPnlArr[riskRednPos].HedgeArr[k].HedgeContracts -
                        #             obj.ClientPnlArr[i].HedgeArr[k].HedgeContracts)
                        #     riskRednClientPnl.HedgeArr[k].HedgeContracts = \
                        #         max(0, riskRednClientPnl.HedgeArr[k].HedgeContracts - self.ClientPnlArr[i].HedgeArr[
                        #             k].HedgeContracts)
                        #     riskRednClientPnl.HPnl = riskRednClientPnl.HPnl - redistributedHedgeCost
                        #     riskRednClientPnl.HedgeArr[k].HedgeCost = \
                        #         riskRednClientPnl.HedgeArr[k].HedgeCost - redistributedHedgeCost

                            # %Additionally set the closed ClientPnl hedgeContracts to 0
                            # self.ClientPnlArr[i].HedgeArr[k].HedgeContracts = 0

            if riskRednClientPnl.Notional == 0:
                self.ClientPnlArr[riskRednPos - 1].RiskRednUsed = True

        if self.Notional > 0 and riskRednClientPnl.Notional > 0:
            self.allocateFIFORiskRednNotional(riskRednClientPnl, riskRednPos)  # TODO: Pass the same pos back?

    # % -----------------------------------------------------------------------------------------
    # % ** *Sets the Status of the RiskPath to close function
    # % -----------------------------------------------------------------------------------------
    def __setRPStatus(self, timestamp, rpStatus):
        if (rpStatus == RiskPathStatus.ForceClose) or (rpStatus == RiskPathStatus.Close):
            self.Status = rpStatus
            self.ClosureDate = timestamp.date()
            self.ClosureTime = timestamp.time()

    # % -----------------------------------------------------------------------------------------
    # % Calculates Cost of Carry by:-
    # % 1. clean price Mtm
    # % 2. Coupon accrual
    # % 3. Funding (Repo) cost
    # % -----------------------------------------------------------------------------------------
    def __calculateCostOfCarry(self, timestamp, clientPnl, p_t1, prevCloseDate):
        if isinstance(prevCloseDate, dt.datetime):
            sd = prevCloseDate.date()
        else:
            sd = prevCloseDate
        if isinstance(timestamp, dt.datetime):
            ed = timestamp.date()
        else:
            ed = timestamp
        # This is for calculating accrued interest from prevDate i.e. sd to curr_date i.e. ed
        lastCouponDate = getLastCouponDate(clientPnl.TradeObj.issue_date,
                                           clientPnl.TradeObj.maturity_date,
                                           clientPnl.TradeObj.coupon_frequency,
                                           self.HolidayCentre,
                                           ed)

        # Check if the current day i.e. ed is a Coupon cashflow.
        nextCouponDate = getNextCouponDate(clientPnl.TradeObj.issue_date,
                                           clientPnl.TradeObj.maturity_date,
                                           clientPnl.TradeObj.coupon_frequency,
                                           self.HolidayCentre,
                                           lastCouponDate)

        # calculate dcf = (settle_date - last_coupon_date).days / (next_coupon - last_coupon).days
        dcf = calculateYearFrac(clientPnl.TradeObj.day_count, lastCouponDate, ed) \
              / calculateYearFrac(clientPnl.TradeObj.day_count, lastCouponDate,
                                  nextCouponDate)  # <-- used for accrued interest

        # This is for accrued coupon between yesterday and today i.e. AI(curr_date) - AI(curr_date - 1)
        # dt (i.e daily) = (ed - prev_date).days / (next_coupon - last_coupon).days
        delta_t_coupon_accrued = calculateYearFrac(clientPnl.TradeObj.day_count, sd, ed)  \
                             / calculateYearFrac(clientPnl.TradeObj.day_count, lastCouponDate,nextCouponDate) # <-- used for daily MtM

        # This is for financing position between curr_date and tomorrow
        # dt (i.e daily) = (curr_date+1 - curr_date).days / (next_coupon - last_coupon).days
        delta_t_financing = calculateYearFrac(clientPnl.TradeObj.day_count, ed, ed + dt.timedelta(days=1)) \
                                 / calculateYearFrac(clientPnl.TradeObj.day_count, lastCouponDate,
                                                     nextCouponDate)  # <-- used for daily MtM
        p_t0 = clientPnl.MidPx
        # accrued = coupon/freq * dcf * Notional
        accruedIncome = calculateAccrued(dcf, clientPnl.TradeObj.coupon,
                                         clientPnl.TradeObj.coupon_frequency) / 100 * clientPnl.Notional

        # calculate the P&L (without the coupon cashflow)
        mtm = (-p_t0 + p_t1) * clientPnl.Notional / 100 + \
              calculateAccrued(delta_t_coupon_accrued, clientPnl.TradeObj.coupon,
                               clientPnl.TradeObj.coupon_frequency)/100 * clientPnl.Notional \
              - (p_t1 / 100 * clientPnl.Notional + accruedIncome) * self.ONRepo * delta_t_financing #<-- financing into future

        # # calculate the P&L (without the coupon cashflow)
        # mtm = (-p_t0 + p_t1) * clientPnl.Notional / 100 + \
        #       (clientPnl.TradeObj.Coupon / getFrequencyNumber(
        #           clientPnl.TradeObj.CouponFrequency)) * dt * clientPnl.Notional \
        #       - (p_t0 / 100 * clientPnl.Notional + accruedIncome) * self.ONRepo * dt

        # Add a coupon cashflow.
        if nextCouponDate == ed:
            clientPnl.CouponRecToday = True
            clientPnl.CouponCF = accruedIncome
            mtm += clientPnl.CouponCF
        else:
            # current businessday is not a coupon cashflow
            if clientPnl.CouponRecToday:
                # coupon cashflow recieved yesterday. So reset it to 0
                clientPnl.CouponRecToday = False
                mtm -= clientPnl.CouponCF  # remove the Coupon which has been recieved
                clientPnl.CouponCF = 0.0  # Reset the prev Coupon

        if not clientPnl.UPnl is None:
            if clientPnl.Side == TradeSide.Bid:
                clientPnl.UPnl += mtm
            else:
                clientPnl.UPnl += -1 * mtm
        else:
            if clientPnl.Side == TradeSide.Bid:
                clientPnl.UPnl = mtm
            else:
                clientPnl.UPnl = -1 * mtm


    # def saveState(self):

    # % -----------------------------------------------------------------------------------------
    # % ** ** ** Checks for existence of: -
    # % 1. an existing client exists
    # % 2. ClientPnlArr exists
    # % -----------------------------------------------------------------------------------------
    @staticmethod
    def calculateClientPnlOnCloseRP(clientPnl, tradedPx):
        """

        :type clientPnl: client_pnl
        """
        assert isinstance(clientPnl, ClientPnl)
        if clientPnl.Side == TradeSide.Bid:
            return (-clientPnl.MidPx + tradedPx) * clientPnl.Notional / 100
        else:
            return (clientPnl.MidPx - tradedPx) * clientPnl.Notional / 100

    @staticmethod
    # % -----------------------------------------------------------------------------------------
    # % Given a new incoming trade (and possible hedges):-
    # % 1. Checks if theres an open RP to allocate this trade to
    # % 2. If not, creates a new RP and allocates the trade to it.
    # % 3. Returns back the update RP_arr
    # % -----------------------------------------------------------------------------------------
    def createOrUpdateRiskPath(timestamp, rp_arr, tr, bIncludeCostOfCarry=None,
                               h_arr=None, closeHedgePxArr = None):

        # No RP exists for given instrument which is in a Open Status. Create a new RP
        bStartNewRP = True
        bSplitRRTrade = False
        tr_new_RP = tr
        if tr.notional > 0 and not tr.trade_added_to_rp:
            # [rp,bStartNewRP,trade] = rp.update(trade,hedge,rpArr);
            for i in range(len(rp_arr)):
                if rp_arr[i].Sym == tr.sym and rp_arr[i].Status == RiskPathStatus.Open:
                    # found the RP to which this trade needs to be added
                    # Now update this rp to calculate ClientPnl
                    bStartNewRP, tr_new_RP, bSplitRRTrade = rp_arr[i].update( timestamp=timestamp,
                                                                              trade=tr,
                                                                              hedge_arr=h_arr,
                                                                              closeHedgePxArr=closeHedgePxArr
                                                                              )
                    tr.RiskPathId = rp_arr[i].RiskPathId

        if bStartNewRP:
            rp = RiskPath(timestamp, tr_new_RP.sym, tr_new_RP.side, tr_new_RP.notional, bIncludeCostOfCarry)

            if bSplitRRTrade:
                if not h_arr is None:
                    for i in range(len(h_arr)):
                        # copy the hedges with Bid/Ask set to current passed in prices
                        h_new_RP = copy.deepcopy(h_arr[i])  # do a deep copy of the existing Hedge
                        h_new_RP.BidPx = closeHedgePxArr[i,0]
                        h_new_RP.AskPx = closeHedgePxArr[i, 1]
                        h_new_RP.MidPx = np.average(closeHedgePxArr[i,:])
                        h_arr[i] = h_new_RP

            # Now update this rp to calculate ClientPnl
            rp.update(timestamp=timestamp,
                      trade=tr_new_RP,
                      hedge_arr=h_arr,
                      closeHedgePxArr=closeHedgePxArr)
            tr_new_RP.RiskPathId = rp.RiskPathId
            # Finally add this rp to rp_arr
            rp_arr.append(rp)

        return rp_arr

    @staticmethod
    # % ------------------------------------------------------------------------------------------------
    # % Does a COB P&L for open RiskPaths:-
    # % Calls the __calculateRolloverMid2MidMarkouts()
    # % -------------------------------------------------------------------------------------------------
    def calcCOBPnlRiskPath(timestamp, rp_arr, closePx, closeHedgePxArr=None, prevCloseDate=None):
        # %perform COB Pnl for each RP in RP_array and store it back into the array.
        for i in range(len(rp_arr)):
            if rp_arr[i].Status == RiskPathStatus.Open:  # %Only if Status is open
                rp_arr[i].rolloverRiskPath(timestamp, closePx, closeHedgePxArr, prevCloseDate)
                rp_arr[i].LastUpdatedTimestamp = timestamp
        return rp_arr

    @staticmethod
    # % ------------------------------------------------------------------------------------------------
    # % Forclose is a COB operation:-
    # % 1. Checks if theres an open RP which needs to be forceClosed (calls rolloverRiskPath())
    # % 2. Goes through the rp_Arr and for rp which are Status=ForceClosed, pyhsicaly closes down the RP
    # % 3. [ASSUMPTION]: ForceClose using D2d or Broker always assumes we close down the FULL RiskPath.
    # % -------------------------------------------------------------------------------------------------
    def checkForceCloseRiskPath(timestamp, rp_arr, askPx, midPx, bidPx,closeHedgePxArr=None):
        for k in range(len(rp_arr)):
            if rp_arr[k].Status == RiskPathStatus.ForceClose:
                rp_arr[k].__forceCloseRiskPathWithD2D(timestamp, rp_arr[k].Notional,
                                                      askPx, midPx, bidPx,closeHedgePxArr)
                rp_arr[k].LastUpdatedTimestamp = timestamp  # <- Also update the timestamp
        return rp_arr

    def __str__(self):
        return "RiskPath: RiskPathId = %s, Sym = %s, StartDate = %s,  CurrentDate = %s, Side = %s, " \
               "Notional = %s, No of ClientPnl = %s" % \
               (self.RiskPathId, self.Sym, self.InitiationDate, self.LastUpdatedTimestamp.date(),
                self.Side, self.Notional, len(self.ClientPnlArr))


if __name__ == "__main__":
    riskPathArr = []

    # ------------------- intra-day ------------------------------------ #
    # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
    date_0 = dt.datetime(2017, 1, 1)
    time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
    # 1.    Create a test trade
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

    # % 2. Create a hedge
    # h = Hedge()

    # Create a new RiskPath from Trade 1
    riskPathArr, tr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr, tr)

    # % % Trade2: Create a second trade
    # date_0 = dt.datetime(2017, 1, 1)
    time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
    tr = Trade()
    tr.TradeId = '222'
    tr.Sym = '9128235'
    tr.Notional = 10 * 1e6
    tr.Side = TradeSide.Bid
    tr.TradedPx = 96.916
    tr.MidPx = 96.93
    tr.ClientSysKey = 222
    tr.Duration = 8.92
    tr.ONRepo = 0.02
    tr.TradeDate = date_0
    tr.Ccy = 'EUR'

    riskPathArr, tr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr, tr)

    # @@@@@@@@@ COB @@@@@@@@@ #
    time_cob = dt.time(18, 0)
    closePx = 96.933
    # First do a COB P&L
    riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_0, time_cob), riskPathArr, closePx)
    # Now do a ForceClose
    MidPx = closePx
    AskPx = MidPx + 0.002
    BidPx = MidPx - 0.002
    riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_0, time_cob),
                                                   riskPathArr,
                                                   AskPx,
                                                   MidPx,
                                                   BidPx)

    # ----------------- New day: T+1 , No new trades --------------- #
    date_1 = date_0 + dt.timedelta(days=1)  # <- new date

    # @@@@@@@@@ COB @@@@@@@@@ #
    time_cob = dt.time(18, 0)
    closePx = 96.934
    # First do a COB P&L
    riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob), riskPathArr, closePx)
    # Now do a ForceClose
    MidPx = closePx
    AskPx = MidPx + 0.002
    BidPx = MidPx - 0.002
    riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_1, time_cob),
                                                   riskPathArr,
                                                   AskPx,
                                                   MidPx,
                                                   BidPx)

    # ----------------- New day: T+2 , No new trades --------------- #
    date_2 = date_1 + dt.timedelta(days=1)  # <- new date

    # @@@@@@@@@ COB @@@@@@@@@ #
    time_cob = dt.time(18, 0)
    closePx = 96.935
    # First do a COB P&L
    riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob), riskPathArr, closePx)
    # Now do a ForceClose
    MidPx = closePx
    AskPx = MidPx + 0.002
    BidPx = MidPx - 0.002
    riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                   riskPathArr,
                                                   AskPx,
                                                   MidPx,
                                                   BidPx)

    # ----------------- New day: T+3 , No new trades --------------- #
    date_3 = date_2 + dt.timedelta(days=1)  # <- new date

    # @@@@@@@@@ COB @@@@@@@@@ #
    time_cob = dt.time(18, 0)
    closePx = 96.936
    # First do a COB P&L
    riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_3, time_cob), riskPathArr, closePx)
    # Now do a ForceClose
    MidPx = closePx
    AskPx = MidPx + 0.002
    BidPx = MidPx - 0.002
    riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_3, time_cob),
                                                   riskPathArr,
                                                   AskPx,
                                                   MidPx,
                                                   BidPx)

    print("Hello World")
