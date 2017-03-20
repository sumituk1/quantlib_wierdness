import aiostreams.operators.operators as op
from common import qc_csv_helper
import numpy as np
from core.markout import GovtBondMarkoutCalculator
from core.trade import Quote,Trade,FixedIncomeTrade
from aiostreams.base import to_async_iterable
import matplotlib.pyplot as plt
from unittest import TestCase


class TestOrderBook(TestCase):
    # Test case for "Buy"
    def test_case_1(self, plotFigure = True):
        tolerance = 5*1e-2
        datapath = "..\\resources\\"  # generally a good idea to use relative paths whenever possible
        quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        trade_files = "trades.csv"

        # Load the quotes data from csv
        quotes_dict = dict()
        for x in quote_files:
            sym, quote = qc_csv_helper.file_to_quote_list(datapath + x)
            quotes_dict[sym] = quote

        # Now get the trades list from csv
        trades_list = qc_csv_helper.file_to_trade_list(datapath + trade_files)

        # Method 2 - go through each of the instruments,
        # create a stream of quote per sym
        quote_trade_list = []
        for k, v in quotes_dict.items():
            # quote_async_iter = to_async_iterable(quotes_dict[k])
            # quote_trade_list.append(quote_async_iter)
            quote_async_iter = to_async_iterable(quotes_dict[k])
            # trades_list_sym = []
            # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

            # trade_async_iter = to_async_iterable(trades_list_sym)
            quote_trade_list.append(quote_async_iter)
            # quote_trade_list.append(trade_async_iter)

        output_list =[]
        trade_async_iter = to_async_iterable(trades_list)
        quote_trade_list.append(trade_async_iter)
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator) | op.flatten() > output_list

        # do assertions
        for mk_msg in output_list:
            if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 0:
                self.assertEquals(np.abs(mk_msg.bps_markout), 0.0, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 60:
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0833))/mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 300:
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.1333)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 300:
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.1333)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == "COB0":
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0722)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == "COB1":
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.844)) / mk_msg.bps_markout), tolerance, msg=None)

        # plot figure
        if plotFigure:
            plt.figure()
            x_data = [x.dt for x in output_list if x.trade_id == "DE10YT_OTR_111"]
            plt.xticks(x_data, ['0','60','3600','COB0','COB1','COB2'])
            plt.plot(x_data,
                     [x.bps_markout for x in output_list if x.trade_id == "DE10YT_OTR_111"],
                     label="markout_bps")
            plt.xlabel("time")
            plt.ylabel("markout(bps)")
            plt.grid(True)
            plt.show()