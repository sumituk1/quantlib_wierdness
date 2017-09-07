from unittest import TestCase
import pickle
import datetime
# from mosaicsmartdata.core.singleton import Singleton
from mosaicsmartdata.core.fx import FXPricingContextGenerator
from mosaicsmartdata.core.instrument_utils import sym_to_instrument
from mosaicsmartdata.core.quote import Quote
from aiostreams import run
import aiostreams.operators as op
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, get_rate, discounting_factor, curve_from_disc_factors


class TestFX(TestCase):

    def test_pricing_context_creation(self):
        with open('../resources/fx/data.pickle', 'rb') as f:
            tiny_quote_dict = pickle.load(f)

        tiny_quotes_list = [quotes for key, quotes in tiny_quote_dict.items()]
        stream = op.merge_sorted(tiny_quotes_list, lambda x: x.timestamp) | \
                 op.map(FXPricingContextGenerator()) > print
        run(stream)

    def detailed_test_pricing_context(self):
        # insert all possible kinds of quotes into the pricing context, and see that it reacts correctly
        instr_gen = sym_to_instrument()
        now = datetime.datetime(2017, 9, 4,0,0,0)
        # create a quote of each type
        syms = ['EUR=','JPY=','EUR1M=','JPY1M=','EURTN=','JPYTN=','USD1MOIS=']
        instrs = [instr_gen(sym,now.date()) for sym in syms]
        mids = [1.5, 100, 10,10, 10,10,1.2]
        quotes = [Quote(instrument=ins, bid=mid, ask=mid, timestamp=now) for ins, mid in zip(instrs, mids)]

        gen = FXPricingContextGenerator()
        gen(quotes[0])
        self.assertEqual(gen.spot_rate['EUR'], 1 / mids[0])
        gen(quotes[1])
        self.assertEqual(gen.spot_rate['JPY'], mids[1])
        gen(quotes[2])
        self.assertEqual(gen.outright_rate['EUR'][instrs[2].maturity_date], 1 / (mids[0] + 0.0001 * mids[2]))
        gen(quotes[3])
        self.assertEqual(gen.outright_rate['JPY'][instrs[3].maturity_date], mids[1] + 0.01 * mids[3])
        gen(quotes[4])
        self.assertEqual(gen.outright_rate['EUR'][instrs[4].settle_date], 1 / (mids[0] - 0.0001 * mids[4]))
        gen(quotes[5])
        self.assertEqual(gen.outright_rate['JPY'][instrs[5].settle_date], mids[1] - 0.01 * mids[5])
        gen(quotes[6])
        self.assertEqual(gen.usd_ois[(instrs[6].spot_settle_date, instrs[6].maturity_date)], mids[6])


if __name__ == '__main__':
    #    unittest.main()
    k= TestFX()
    #k.setUp()
    k.detailed_test_pricing_context()