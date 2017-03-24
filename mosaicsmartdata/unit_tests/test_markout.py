from unittest import TestCase
import numpy as np
import aiostreams.operators.operators as op
from aiostreams.base import to_async_iterable
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.core.markout import GovtBondMarkoutCalculator


class TestMarkouts(TestCase):
    # Test for Sell in bps over intra-day to COB1
    def test_case_1(self, plotFigure = False):
        tolerance = 5*1e-2
        datapath = "..\\resources\\"  # generally a good idea to use relative paths whenever possible
        quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        trade_files = "trades.csv"

        # Load the quotes data from csv
        quotes_dict = dict()
        for x in quote_files:
            sym, quote = qc_csv_helper.file_to_quote_list(datapath + x, MarkoutMode.Unhedged)
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
        joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten() > output_list

        # do assertions
        self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
        for mk_msg in output_list:
            if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '0':
                self.assertEquals(np.abs(mk_msg.bps_markout), 0.0, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-900':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.15)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-60':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.022) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0833))/mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.1333)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.572)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0722)) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.844)) / mk_msg.bps_markout), tolerance, msg=None)

        # plot figure
        # if plotFigure:
        #     plt.figure()
        #     x_data = [x.dt for x in output_list if x.trade_id == "DE10YT_OTR_111"]
        #     plt.xticks(x_data, ['0','60','3600','COB0','COB1','COB2'])
        #     plt.plot(x_data,
        #              [x.bps_markout for x in output_list if x.trade_id == "DE10YT_OTR_111"],
        #              label="markout_bps")
        #     plt.xlabel("time")
        #     plt.ylabel("markout(bps)")
        #     plt.grid(True)
        #     plt.show()

    # Test for Sell in cents over intra-day to COB1
    def test_case_2(self, plotFigure=False):
        tolerance = 5 * 1e-2
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

        output_list = []
        trade_async_iter = to_async_iterable(trades_list)
        quote_trade_list.append(trade_async_iter)
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten() > output_list

        # do assertions
        self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
        for mk_msg in output_list:
            if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '0':
                self.assertEquals(np.abs(mk_msg.cents_markout), 0.0, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - (-1.50)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - (-2.40)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - (-10.30)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - (-1.30)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - (-15.20)) / mk_msg.bps_markout), tolerance,
                                     msg=None)

    # Test for Buy in bps over intra-day to COB1
    def test_case_3(self, plotFigure=False):
        tolerance = 5 * 1e-2
        tolerance = 5 * 1e-2
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

        output_list = []
        trade_async_iter = to_async_iterable(trades_list)
        quote_trade_list.append(trade_async_iter)
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten() > output_list

        # do assertions
        self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)

        for mk_msg in output_list:
            if mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '0':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.38)/mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.47) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.51) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.57) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.0722) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.844) / mk_msg.bps_markout), tolerance, msg=None)

    # Test for Buy in cents over intra-day to COB1
    def test_case_4(self, plotFigure=False):
        tolerance = 5 * 1e-2
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

        output_list = []
        trade_async_iter = to_async_iterable(trades_list)
        quote_trade_list.append(trade_async_iter)
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten() > output_list

        # do assertions
        self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)

        for mk_msg in output_list:
            if mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '0':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - 6.90) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - 8.40) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - 9.10) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - 10.20) / mk_msg.bps_markout), tolerance, msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - 1.30) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.cents_markout - 15.20) / mk_msg.bps_markout), tolerance, msg=None)

    # ONLY COB markouts. Make sure the config file has only got COB0, COB1 and COB2 in lags_list
    def test_case_5(self, plotFigure=False):
        tolerance = 5 * 1e-2
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

        output_list = []
        trade_async_iter = to_async_iterable(trades_list)
        quote_trade_list.append(trade_async_iter)
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator(lags_list=['COB0','COB1','COB2'])) \
        | op.flatten() > output_list

        # do assertions
        self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
        self.assertEquals(len(output_list), 9, msg=None)
        for mk_msg in output_list:
            if mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.072) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.844) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB2':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-1.138)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "UST30Y_OTR_111111" and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-1.128)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "UST30Y_OTR_111111" and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-9.85)) / mk_msg.bps_markout), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == "UST30Y_OTR_111111" and mk_msg.dt == 'COB2':
                self.assertLessEqual(np.abs((mk_msg.bps_markout - (-13.41)) / mk_msg.bps_markout), tolerance,
                                     msg=None)