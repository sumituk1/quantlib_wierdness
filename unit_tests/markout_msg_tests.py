from unittest import TestCase
from mosaicsmartdata.core.markout_msg import MarkoutMessage2
from mosaicsmartdata.core.trade import FixedIncomeBondTrade
from mosaicsmartdata.core.quote import Quote

class TestMarkoutMessage(TestCase):
    # Test for Sell in bps over intra-day to COB1
    def test_case_1(self):
        q = Quote(bid=1, ask=2)
        self.assertEqual(q.mid, 1.5)

    def test_case_2(self):
        t = FixedIncomeBondTrade(trade_id=1, duration=20, notional=5)
        msg = MarkoutMessage2(trade=t, price_markout=1)

        self.assertEqual(msg.bps_markout, 5.0)
        self.assertEqual(msg.cents_markout, 100.0)
        self.assertEqual(msg.PV_markout, 0.01)
        self.assertEqual(msg.price_markout, 1)

