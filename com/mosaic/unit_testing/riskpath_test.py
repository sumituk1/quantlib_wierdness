# from __future__ import print_function
import unittest

from com.mosaic.core.hedge import *
from com.mosaic.core.trade import *

from core.riskpath import *


class RiskPathTest(unittest.TestCase):
    # Test case 1 & 2 in spreadsheet
    def test_case_1_2(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                               tr, bIncludeCostOfCarry=False, h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

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
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob), riskPathArr, closePx,date_0)
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

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.ForceClose,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 0, tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1260), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1800), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].UPnl, None, msg=None)  # check UPnl for HYPOTHETICAL d2d Trade
        self.assertLessEqual(riskPathArr[0].ClientPnlArr[-1].TradeObj.trade_id, "HYPOTHETICAL BROKER TRADE",
                             msg=None)  # check trade_id for HYPOTHETICAL d2d Trade

    # Test case 3 : Simple RiskRedn trade check (ForceClose)
    def test_case_3(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date

        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 3.5 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.935
        tr.mid_px = 96.934
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
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

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 13.5 * 1e6, tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1260), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1900), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[-1].UPnl - 35), tolerance_dollar,
                             msg=None)  # check Upnl of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRedn, True, msg=None)  # check Status of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRednUsed, True,
                          msg=None)  # check whether all of RiskRedn trade was used

    # Test case 4 : RiskRedn trade with -ve Pnl redistributed across first trade only (partial closeoff)
    def test_case_4(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date

        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 3.5 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.933  # Trading through Mid!!
        tr.mid_px = 96.934
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
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

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 13.5 * 1e6, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1225), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1900), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[-1].UPnl - 0), tolerance_dollar,
                             msg=None)  # check Upnl of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRedn, True, msg=None)  # check Status of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRednUsed, True,
                          msg=None)  # check whether all of RiskRedn trade was used

    # Test case 5 : RiskRedn trade with -ve Pnl redistributed across 2 trades (partial closeoff)
    def test_case_5(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date

        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 8.0 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.933  # Trading through Mid!!
        tr.mid_px = 96.934
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
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

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 9.0 * 1e6, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1120), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1870), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[-1].UPnl - 0), tolerance_dollar,
                             msg=None)  # check Upnl of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRedn, True, msg=None)  # check Status of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRednUsed, True,
                          msg=None)  # check whether all of RiskRedn trade was used

    # Test case 6 : RiskRedn trade with -ve Pnl redistributed across 2 trades and ForceClosed (partial closeoff)
    def test_case_6(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date
        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 8.0 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.933  # Trading through Mid!!
        tr.mid_px = 96.934
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
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

        # @@@@@@@@@ COB T2 @@@@@@@@@ #
        date_1 = date_1 + dt.timedelta(days=1)  # <- new date
        time_cob = dt.time(18, 0)
        closePx = 96.936
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

        # @@@@@@@@@ COB T3 @@@@@@@@@ #
        date_1 = date_1 + dt.timedelta(days=1)  # <- new date
        time_cob = dt.time(18, 0)
        closePx = 96.937
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

        # ASSERTIONS
        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status,
                             RiskPathStatus.Open,msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 9.0 * 1e6,
                             tolerance_dollar,msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1120),
                             tolerance_dollar,msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1870),
                             tolerance_dollar,msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[-2].UPnl - 0),
                             tolerance_dollar,msg=None)  # check Upnl of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-2].RiskRedn, True,msg=None)  # check Status of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-2].RiskRednUsed,
                          True,msg=None)  # check whether all of RiskRedn trade was used
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].TradeObj.trade_id,
                          "HYPOTHETICAL BROKER TRADE",msg=None)  # check whether all of RiskRedn trade was used

    # Test case 7 : RiskRedn trade with closing down a RP and starting a new one - Split Trade
    def test_case_7(self):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade. Split the trade. --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date
        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 25.0 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.934  # Trading through Mid!!
        tr.mid_px = 96.935
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.936
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

        # ASSERTIONS
        self.assertLessEqual(len(riskPathArr), 2, msg=None)  # 2 riskpaths
        self.assertLessEqual(riskPathArr[0].Status,
                             RiskPathStatus.Close,msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 0,
                             tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(riskPathArr[1].Notional - 8000000,
                             tolerance_dollar, msg=None)  # 2nd riskpath notional = 8 mil
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1190),
                             tolerance_dollar,msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1700),
                             tolerance_dollar,msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[-1].UPnl - 0),
                             tolerance_dollar,msg=None)  # check UPnl for ClientPnl_3 SplitTrade
        self.assertLessEqual(np.abs(riskPathArr[1].ClientPnlArr[0].UPnl - (-160)),
                             tolerance_dollar,msg=None)  # check Upnl of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRedn,
                          True, msg=None)  # check Status of RiskRedn trade
        self.assertEquals(riskPathArr[0].ClientPnlArr[-1].RiskRednUsed,
                          True,msg=None)  # check whether all of RiskRedn trade was used

    # Test case 8 : RiskRedn trade with -ve Pnl redistributed across 2 trades and ForceClosed (
    # complete closeoff) + test for RiskPathClosureTol
    def test_case_8(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date
        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 17.4 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.933  # Trading through Mid!!
        tr.mid_px = 96.934
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
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

        # ASSERTIONS
        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Close,
                             msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 0, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1118), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1597), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[-1].UPnl - 0), tolerance_dollar,
                             msg=None)  # check Upnl of RiskRedn trade

    # Test case 9 : Similar to Case 7. Also adds a RiskRedn trade on the newly initiated RP.
    # ForceCloses the second RP. First RP is client trade de-activated
    def test_case_9(self):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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
        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade2: Create a second trade
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T0 @@@@@@@@@ #
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

        # ----------------- New day: T+1 , 1 Risk-redn trade. Split the trade. --------------- #
        date_1 = date_0 + dt.timedelta(days=1)  # <- new date
        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 25.0 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.934  # Trading through Mid!!
        tr.mid_px = 96.935
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # % % Trade 3: Create a 3rd trade. This is a risk redn trade
        time_0 = dt.time(14, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '777'
        tr.sym = '9128235'
        tr.notional = 6.5 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.935  # Trading through Mid!!
        tr.mid_px = 96.936
        tr.client_key = 777
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_1, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=False,h_arr=None)

        # @@@@@@@@@ COB T1 @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.937
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

        # @@@@@@@@@ COB T2 @@@@@@@@@ #
        date_1 = date_1 + dt.timedelta(days=1)  # <- new date
        time_cob = dt.time(18, 0)
        closePx = 96.947
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

        # @@@@@@@@@ COB T3 @@@@@@@@@ #
        date_1 = date_1 + dt.timedelta(days=1)  # <- new date
        time_cob = dt.time(18, 0)
        closePx = 96.957
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

        # @@@@@@@@@ COB T4 @@@@@@@@@ #
        date_1 = date_1 + dt.timedelta(days=1)  # <- new date
        time_cob = dt.time(18, 0)
        closePx = 96.967
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

        # ASSERTIONS
        self.assertLessEqual(len(riskPathArr), 2, msg=None)  # 2 riskpaths
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Close,
                             msg=None)  # riskpath status should be ForceClose
        self.assertLessEqual(riskPathArr[0].Notional - 0, tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(riskPathArr[1].Notional - 0, tolerance_dollar,msg=None)  # 2nd riskpath forceclosed
        self.assertLessEqual(np.abs(riskPathArr[1].ClientPnlArr[0].UPnl - (-590)), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[1].ClientPnlArr[1].UPnl - 65),
                             tolerance_dollar,msg=None)  # check UPnl for ClientPnl_2
        self.assertEquals(riskPathArr[1].ClientPnlArr[-1].UPnl, None,msg=None)  # check UPnl for HYPOTHETICAL D2D trade
        self.assertLessEqual(riskPathArr[1].ClosureDate,
                             dt.date(2017,1,5),msg=None)  # check "force" closureDate for RP 2
        self.assertEquals(riskPathArr[0].Status,
                          RiskPathStatus.Close, msg=None)  # check status for 1st RP
        self.assertEquals(riskPathArr[1].Status,
                          RiskPathStatus.ForceClose, msg=None)  # check status for 2nd RP

    # ------------ COST-OF-CARRY + ACCRUED + DAYCOUNT/FREQUENCY TESTS ---------------- #
    # Test case for ON Repo -> Set the config file for doing Cost-of-carry calc
    def test_case_10(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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
        # Instrument static
        tr.coupon=0.02
        tr.coupon_frequency = Frequency.ANNUAL
        tr.issue_date = dt.datetime(2010,6,1)
        tr.maturity_date = dt.datetime(2020, 6, 1)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=None,h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.ANNUAL
        tr.issue_date = dt.datetime(2010, 6, 1)
        tr.maturity_date = dt.datetime(2020, 6, 1)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr,bIncludeCostOfCarry=None,h_arr=None)

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
        # First do a COB P&L.
        # NOTE: Pass is a None for hedgePxArr so that the Cost-of-carry is calculated
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx,None,date_0)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_1, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17*1e6, tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1606), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 2294), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2

    # Test case for ON Repo but with a coupon cashflow on T+1( reset back the coupon on T+2)
    def test_case_10b(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.ANNUAL
        tr.issue_date = dt.datetime(2010, 2, 1)
        tr.maturity_date = dt.datetime(2020, 1, 2)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=None, h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.ANNUAL
        tr.issue_date = dt.datetime(2010, 1, 2)
        tr.maturity_date = dt.datetime(2020, 1, 2)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=None, h_arr=None)

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
        # First do a COB P&L.
        # NOTE: Pass is a None for hedgePxArr so that the Cost-of-carry is calculated
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, None, date_0)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_1, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        date_2 = date_1 + dt.timedelta(days=1)  # <- new date

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx,None,date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17 * 1e6, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 2032)/2032, 0.02,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 2902)/2902, 0.02,
                             msg=None)  # check UPnl for ClientPnl_2

    # Test case for ON Repo -> Similar to Use Case 10 but with (SEMI coupon Freq)
    def test_case_10c(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.SEMI
        tr.issue_date = dt.datetime(2010, 6, 2)
        tr.maturity_date = dt.datetime(2020, 6, 2)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=None, h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.SEMI
        tr.issue_date = dt.datetime(2010, 6, 2)
        tr.maturity_date = dt.datetime(2020, 6, 2)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=None, h_arr=None)

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
        # First do a COB P&L.
        # NOTE: Pass is a None for hedgePxArr so that the Cost-of-carry is calculated
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, None, date_0)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_1, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17 * 1e6, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1574), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 2249), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2

    # Test case for ON Repo -> Similar to Use Case 10c but with (SEMI coupon Freq) +
    # Coupon on T+2 day
    # Forclose on T+3
    def test_case_10d(self, plotFigure=True):
        tolerance_dollar = 0.02
        riskPathArr = []

        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.SEMI
        tr.issue_date = dt.datetime(2010, 1, 2)
        tr.maturity_date = dt.datetime(2020, 1, 2)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        # % 2. Create a hedge
        # h = Hedge()

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=None, h_arr=None)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        # Instrument static
        tr.coupon = 0.02
        tr.coupon_frequency = Frequency.SEMI
        tr.issue_date = dt.datetime(2010, 1, 2)
        tr.maturity_date = dt.datetime(2020, 1, 2)
        tr.day_count = DayCountConv.ACT_360
        tr.calculate_trade_dv01()

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=None, h_arr=None)

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
        # First do a COB P&L.
        # NOTE: Pass is a None for hedgePxArr so that the Cost-of-carry is calculated
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, None, date_0)
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
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx,None, date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        # ----------------- New day: T+3 , No new trades ForceClose after doing a P&L --------------- #
        date_3 = date_2 + dt.timedelta(days=1)  # <- new date

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.936
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_3, time_cob),
                                                  riskPathArr, closePx,closeHedgePxArr=None,
                                                  prevCloseDate=date_2)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_3, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17 * 1e6, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 2204)/2204, tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 3146)/3146, tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2

    # -------  HEDGING TESTS -------------- #
    # Test case 11 - Futures hedging with 2 BondFutures
    def test_case_11(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []
        hedgeArr = []
        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")

        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge 1
        h1 = Hedge()
        h1.AskPx = 110.2095
        h1.BidPx = 110.2000
        h1.MidPx = (h1.AskPx + h1.BidPx)/2
        h1.DV01 = 94.65
        h1.IsFutures = True
        h1.TradeObj = tr
        h1.sym = tr.sym
        h1.Beta = 0.56
        h1.HedgeNotional = 100000
        h1.calculate_initial_hedge_cost()
        hedgeArr.append(h1)

        # % Create a hedge 2
        h2 = Hedge()
        h2.AskPx = 163.75
        h2.BidPx = 163.73
        h2.MidPx = (h2.AskPx + h2.BidPx)/2
        h2.DV01 = 85
        h2.IsFutures = True
        h2.TradeObj = tr
        h2.sym = tr.sym
        h2.Beta = 0.85
        h2.HedgeNotional = 100000
        h2.calculate_initial_hedge_cost()
        hedgeArr.append(h2)

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        hedgeArr = []

        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        # % 2. Create a hedge 1
        h3 = Hedge()
        h3.AskPx = 110.2085
        h3.BidPx = 110.1990
        h3.MidPx = (h3.AskPx + h3.BidPx)/2
        h3.DV01 = 94.65
        h3.IsFutures = True
        h3.TradeObj = tr
        h3.sym = tr.sym
        h3.Beta = 0.56
        h3.HedgeNotional = 100000
        h3.calculate_initial_hedge_cost()
        hedgeArr.append(h3)

        # % Create a hedge 2
        h4 = Hedge()
        h4.AskPx = 163.749
        h4.BidPx = 163.729
        h4.MidPx = (h4.AskPx+ h4.BidPx)/2
        h4.DV01 = 85
        h4.IsFutures = True
        h4.TradeObj = tr
        h4.sym = tr.sym
        h4.Beta = 0.85
        h4.HedgeNotional = 100000
        h4.calculate_initial_hedge_cost()
        hedgeArr.append(h4)

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.933
        closeHedgePxArr = [110.2027, 163.7380]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_0, time_cob),
                                                  riskPathArr, closePx,closeHedgePxArr)
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
        closeHedgePxArr = [110.2017, 163.7370]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx,closeHedgePxArr,
                                                  date_0)
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
        closeHedgePxArr = [110.2007, 163.7360]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx,closeHedgePxArr,date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17000000, tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1330), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1900), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].HPnl - (-399)), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].HPnl - (-715)), tolerance_dollar,
                         msg=None)  # check UPnl for ClientPnl_2

        # Test case 11 - Futures hedging with 2 BondFutures

    # Test case 12 - Futures hedging with 2 BondFutures and force-close after 3 days with hedge unwind
    def test_case_12(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []
        hedgeArr = []
        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")

        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge 1
        h1 = Hedge()
        h1.AskPx = 110.2095
        h1.BidPx = 110.2000
        h1.MidPx = (h1.AskPx + h1.BidPx) / 2
        h1.DV01 = 94.65
        h1.IsFutures = True
        h1.TradeObj = tr
        h1.sym = tr.sym
        h1.Beta = 0.56
        h1.HedgeNotional = 100000
        h1.calculate_initial_hedge_cost()
        hedgeArr.append(h1)

        # % Create a hedge 2
        h2 = Hedge()
        h2.AskPx = 163.75
        h2.BidPx = 163.73
        h2.MidPx = (h2.AskPx + h2.BidPx) / 2
        h2.DV01 = 85
        h2.IsFutures = True
        h2.TradeObj = tr
        h2.sym = tr.sym
        h2.Beta = 0.85
        h2.HedgeNotional = 100000
        h2.calculate_initial_hedge_cost()
        hedgeArr.append(h2)

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        hedgeArr = []

        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        # % 2. Create a hedge 1
        h3 = Hedge()
        h3.AskPx = 110.2085
        h3.BidPx = 110.1990
        h3.MidPx = (h3.AskPx + h3.BidPx) / 2
        h3.DV01 = 94.65
        h3.IsFutures = True
        h3.TradeObj = tr
        h3.sym = tr.sym
        h3.Beta = 0.56
        h3.HedgeNotional = 100000
        h3.calculate_initial_hedge_cost()
        hedgeArr.append(h3)

        # % Create a hedge 2
        h4 = Hedge()
        h4.AskPx = 163.749
        h4.BidPx = 163.729
        h4.MidPx = (h4.AskPx + h4.BidPx) / 2
        h4.DV01 = 85
        h4.IsFutures = True
        h4.TradeObj = tr
        h4.sym = tr.sym
        h4.Beta = 0.85
        h4.HedgeNotional = 100000
        h4.calculate_initial_hedge_cost()
        hedgeArr.append(h4)

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.933
        closeHedgePxArr = [110.2027, 163.7380]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_0, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr)
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
        closeHedgePxArr = [110.2017, 163.7370]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr,
                                                  date_0)
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
        closeHedgePxArr = [110.2007, 163.7360]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr, date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        # ----------------- New day: T+3 , No new trades (Force Close) --------------- #
        date_3 = date_2 + dt.timedelta(days=1)  # <- new date

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.936
        closeHedgePxArr = [110.1997, 163.7350]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_3, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr, date_2)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        closeHedgePxArr = np.array([
                                    [110.1950,110.2045],
                                    [163.725,163.745]
                                    ])
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_3, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx,
                                                       closeHedgePxArr)

        # ----- check assertions -------
        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17000000, tolerance_dollar, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1260), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1800), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].HPnl - (-1095)), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].HPnl - (-1714)), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2

    # Test case 13 - Futures hedging with 2 BondFutures , 1 RR traded on T+2 and forclose after 2 days with hedge unwind
    def test_case_13(self, plotFigure=True):
        tolerance_percent = 3*1e-2  # 2%
        riskPathArr = []
        hedgeArr = []
        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")

        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge 1
        h1 = Hedge()
        h1.AskPx = 110.2095
        h1.BidPx = 110.2000
        h1.MidPx = (h1.AskPx + h1.BidPx) / 2
        h1.DV01 = 94.65
        h1.IsFutures = True
        h1.TradeObj = tr
        h1.sym = tr.sym
        h1.Beta = 0.56
        h1.HedgeNotional = 100000
        h1.calculate_initial_hedge_cost()
        hedgeArr.append(h1)

        # % Create a hedge 2
        h2 = Hedge()
        h2.AskPx = 163.75
        h2.BidPx = 163.73
        h2.MidPx = (h2.AskPx + h2.BidPx) / 2
        h2.DV01 = 85
        h2.IsFutures = True
        h2.TradeObj = tr
        h2.sym = tr.sym
        h2.Beta = 0.85
        h2.HedgeNotional = 100000
        h2.calculate_initial_hedge_cost()
        hedgeArr.append(h2)

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        hedgeArr = []

        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        # % 2. Create a hedge 1
        h3 = Hedge()
        h3.AskPx = 110.2085
        h3.BidPx = 110.1990
        h3.MidPx = (h3.AskPx + h3.BidPx) / 2
        h3.DV01 = 94.65
        h3.IsFutures = True
        h3.TradeObj = tr
        h3.sym = tr.sym
        h3.Beta = 0.56
        h3.HedgeNotional = 100000
        h3.calculate_initial_hedge_cost()
        hedgeArr.append(h3)

        # % Create a hedge 2
        h4 = Hedge()
        h4.AskPx = 163.749
        h4.BidPx = 163.729
        h4.MidPx = (h4.AskPx + h4.BidPx) / 2
        h4.DV01 = 85
        h4.IsFutures = True
        h4.TradeObj = tr
        h4.sym = tr.sym
        h4.Beta = 0.85
        h4.HedgeNotional = 100000
        h4.calculate_initial_hedge_cost()
        hedgeArr.append(h4)

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.933
        closeHedgePxArr = [110.2027, 163.7380]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_0, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr)
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
        closeHedgePxArr = [110.2017, 163.7370]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr,
                                                  date_0)
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

        # Create a RR trade
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 7.5 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.9335
        tr.mid_px = 96.9345
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_2
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        closeHedgePxArr = np.array([[110.2012, 110.2107],
                                    [163.7365, 163.7565]
                                    ])
        # unwind/readjust the hedges
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr,
                                                      closeHedgePxArr = closeHedgePxArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
        closeHedgePxArr = [110.2007, 163.7360]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr, date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        # ----------------- New day: T+3 , No new trades (Force Close) --------------- #
        date_3 = date_2 + dt.timedelta(days=1)  # <- new date

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.936
        closeHedgePxArr = [110.1997, 163.7350]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_3, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr, date_2)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        closeHedgePxArr = np.array([
            [110.1950, 110.2045],
            [163.725, 163.745]])
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_3, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx,
                                                       closeHedgePxArr)

        # ----- check assertions -------
        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.ForceClose,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].ClientPnlArr[2].RiskRedn, True,
                             msg=None)  # second trade was a RR trade
        self.assertLessEqual(len(riskPathArr[0].ClientPnlArr[2].HedgeArr), 0,
                             msg=None)  # second trade was a RR trade. So no hedges
        self.assertLessEqual(riskPathArr[0].Notional - 0, tolerance_percent, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1155)/1155, tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1748)/1748, tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].HPnl - (-2039))/abs(2039), tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].HPnl - (-1633))/abs(1633), tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_2

    # Test case 14 - Futures hedging with 2 BondFutures , 1 RR traded on T+2 and Split RR trade
    def test_case_14(self, plotFigure=True):
        tolerance_percent = 3 * 1e-2  # 2%
        riskPathArr = []
        hedgeArr = []
        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")

        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge 1
        h1 = Hedge()
        h1.AskPx = 110.2095
        h1.BidPx = 110.2000
        h1.MidPx = (h1.AskPx + h1.BidPx) / 2
        h1.DV01 = 94.65
        h1.IsFutures = True
        h1.TradeObj = tr
        h1.sym = tr.sym
        h1.Beta = 0.56
        h1.HedgeNotional = 100000
        h1.calculate_initial_hedge_cost()
        hedgeArr.append(h1)

        # % Create a hedge 2
        h2 = Hedge()
        h2.AskPx = 163.75
        h2.BidPx = 163.73
        h2.MidPx = (h2.AskPx + h2.BidPx) / 2
        h2.DV01 = 85
        h2.IsFutures = True
        h2.TradeObj = tr
        h2.sym = tr.sym
        h2.Beta = 0.85
        h2.HedgeNotional = 100000
        h2.calculate_initial_hedge_cost()
        hedgeArr.append(h2)

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        hedgeArr = []

        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        # % 2. Create a hedge 1
        h3 = Hedge()
        h3.AskPx = 110.2085
        h3.BidPx = 110.1990
        h3.MidPx = (h3.AskPx + h3.BidPx) / 2
        h3.DV01 = 94.65
        h3.IsFutures = True
        h3.TradeObj = tr
        h3.sym = tr.sym
        h3.Beta = 0.56
        h3.HedgeNotional = 100000
        h3.calculate_initial_hedge_cost()
        hedgeArr.append(h3)

        # % Create a hedge 2
        h4 = Hedge()
        h4.AskPx = 163.749
        h4.BidPx = 163.729
        h4.MidPx = (h4.AskPx + h4.BidPx) / 2
        h4.DV01 = 85
        h4.IsFutures = True
        h4.TradeObj = tr
        h4.sym = tr.sym
        h4.Beta = 0.85
        h4.HedgeNotional = 100000
        h4.calculate_initial_hedge_cost()
        hedgeArr.append(h4)

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.933
        closeHedgePxArr = [[110.1980,110.2075],[163.728,163.748]]
                # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_0, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr)
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
        closeHedgePxArr = [[110.1970,110.2065], [163.727,163.747]]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr,
                                                  date_0)
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

        # Create a RR trade
        tr = FixedIncomeTrade()
        tr.trade_id = '333'
        tr.sym = '9128235'
        tr.notional = 20 * 1e6
        tr.side = TradeSide.Ask
        tr.traded_px = 96.9335
        tr.mid_px = 96.9345
        tr.client_key = 333
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_2
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        closeHedgePxArr = np.array([[110.2012, 110.2107],
                                    [163.7365, 163.7565]
                                    ])
        # unwind/readjust the hedges
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr,
                                                      closeHedgePxArr=closeHedgePxArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.935
        closeHedgePxArr = np.array([[110.2002,110.2097],
                                    [163.7355,163.7555]]
                                   )
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr, date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)
        self.assertLessEqual(len(riskPathArr), 2, msg=None)  # 2 riskpaths
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.ForceClose,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].ClientPnlArr[2].RiskRedn, True,
                             msg=None)  # second trade was a RR trade
        self.assertLessEqual(len(riskPathArr[0].ClientPnlArr[2].HedgeArr), 0,
                             msg=None)  # second trade was a RR trade. So no hedges
        self.assertLessEqual(riskPathArr[0].Notional - 0, tolerance_percent, msg=None)  # riskpath notional = 0
        self.assertLessEqual(riskPathArr[1].Notional - 3000000, tolerance_percent, msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1155) / 1155, tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].HPnl - (-2039)) / abs(-2039), tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1650) / 1650, tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].HPnl - (-3068)) / abs(-3068), tolerance_percent,
                         msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[1].ClientPnlArr[0].UPnl - (-45)) / abs(-45), tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[1].ClientPnlArr[0].HPnl - (-389)) / abs(-389), tolerance_percent,
                             msg=None)  # check UPnl for ClientPnl_2

    # Test case 15 - 1 Futures + 1 Cash hedging. No Force-closes
    def test_case_15(self, plotFigure=True):
        tolerance_dollar = 10  # bps
        riskPathArr = []
        hedgeArr = []
        # ------------------- intra-day ------------------------------------ #
        # % % Trade1: Run a test to create a new RiskPath. NO HEDGES
        date_0 = dt.datetime(2017, 1, 2)
        time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")

        # 1.    Create a test trade
        tr = FixedIncomeTrade()
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

        # % 2. Create a hedge 1
        h1 = Hedge()
        h1.AskPx = 110.2095
        h1.BidPx = 110.2000
        h1.MidPx = (h1.AskPx + h1.BidPx) / 2
        h1.DV01 = 94.65
        h1.IsFutures = True
        h1.TradeObj = tr
        h1.sym = tr.sym
        h1.Beta = 0.56
        h1.HedgeNotional = 100000
        h1.calculate_initial_hedge_cost()
        hedgeArr.append(h1)

        # % Create a hedge 2 - This is a Cash Hedge
        h2 = Hedge()
        h2.AskPx = 163.75
        h2.BidPx = 163.73
        h2.MidPx = (h2.AskPx + h2.BidPx) / 2
        h2.DV01 = 6.5*1e-4  # <-- DV01 per bps per $1
        h2.IsFutures = False
        h2.TradeObj = tr
        h2.sym = tr.sym
        h2.Beta = 0.85
        # h2.Hedgenotional = 100000
        h2.calculate_initial_hedge_cost()
        hedgeArr.append(h2)

        # Create a new RiskPath from Trade 1
        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # % % Trade2: Create a second trade
        # date_0 = dt.datetime(2017, 1, 1)
        hedgeArr = []

        time_0 = dt.time(11, 23)  # .strftime("%H:%M:%S")
        tr = FixedIncomeTrade()
        tr.trade_id = '222'
        tr.sym = '9128235'
        tr.notional = 10 * 1e6
        tr.side = TradeSide.Bid
        tr.traded_px = 96.916
        tr.mid_px = 96.93
        tr.client_key = 222
        tr.duration = 8.92
        tr.on_repo = 0.02
        tr.trade_date = date_0
        tr.ccy = 'EUR'
        tr.calculate_trade_dv01()

        # % 2. Create a hedge 1
        h3 = Hedge()
        h3.AskPx = 110.2085
        h3.BidPx = 110.1990
        h3.MidPx = (h3.AskPx + h3.BidPx) / 2
        h3.DV01 = 94.65
        h3.IsFutures = True
        h3.TradeObj = tr
        h3.sym = tr.sym
        h3.Beta = 0.56
        h3.HedgeNotional = 100000
        h3.calculate_initial_hedge_cost()
        hedgeArr.append(h3)

        # % Create a hedge 2
        h4 = Hedge()
        h4.AskPx = 163.749
        h4.BidPx = 163.729
        h4.MidPx = (h4.AskPx + h4.BidPx) / 2
        h4.DV01 = 6.5*1e-4
        h4.IsFutures = False
        h4.TradeObj = tr
        h4.sym = tr.sym
        h4.Beta = 0.85
        # h4.Hedgenotional = 100000
        h4.calculate_initial_hedge_cost()
        hedgeArr.append(h4)

        riskPathArr = RiskPath.createOrUpdateRiskPath(dt.datetime.combine(date_0, time_0), riskPathArr,
                                                      tr, bIncludeCostOfCarry=False, h_arr=hedgeArr)

        # @@@@@@@@@ COB @@@@@@@@@ #
        time_cob = dt.time(18, 0)
        closePx = 96.933
        closeHedgePxArr = [110.2027, 163.7380]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_0, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr)
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
        closeHedgePxArr = [110.2017, 163.7370]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_1, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr,
                                                  date_0)
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
        closeHedgePxArr = [110.2007, 163.7360]
        # First do a COB P&L
        riskPathArr = RiskPath.calcCOBPnlRiskPath(dt.datetime.combine(date_2, time_cob),
                                                  riskPathArr, closePx, closeHedgePxArr, date_1)
        # Now do a ForceClose
        MidPx = closePx
        AskPx = MidPx + 0.002
        BidPx = MidPx - 0.002
        riskPathArr = RiskPath.checkForceCloseRiskPath(dt.datetime.combine(date_2, time_cob),
                                                       riskPathArr,
                                                       AskPx,
                                                       MidPx,
                                                       BidPx)

        # ----- check assertions --------------------------------------------------------------
        self.assertLessEqual(len(riskPathArr), 1, msg=None)  # only 1 riskpath
        self.assertLessEqual(riskPathArr[0].Status, RiskPathStatus.Open,
                             msg=None)  # riskpath status should be "ForceClose"
        self.assertLessEqual(riskPathArr[0].Notional - 17000000, tolerance_dollar,
                             msg=None)  # riskpath notional = 0
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].UPnl - 1330), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].UPnl - 1900), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[0].HPnl - (-517)), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_1
        self.assertLessEqual(np.abs(riskPathArr[0].ClientPnlArr[1].HPnl - (-908)), tolerance_dollar,
                             msg=None)  # check UPnl for ClientPnl_2

if __name__ == '__main__':
    unittest.main()
