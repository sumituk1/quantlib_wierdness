import importlib
import logging

importlib.reload(logging)
# logging.basicConfig(level = logging.INFO)
from unittest import TestCase
import numpy as np
import aiostreams.operators as op
from aiostreams import run, ExceptionLoggingContext
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.common.read_config import Configurator
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.core.markout import GovtBondMarkoutCalculator
import time
import os, inspect

thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
os.chdir(thisfiledir)


class TestMarkouts(TestCase):
    # 1. function to read files & importlib
    # 2. to run the graph
    #


    # def setUp(self):
        # self.config = QCConfigProvider()

    # function to read the quotes and trade file and merge them to a iterable list
    def read_and_merge_quotes_trade(self, datapath, quote_file_list, trade_file):
        # get the trades list from csv
        trades_list = qc_csv_helper.file_to_trade_list(datapath + trade_file)

        # Load the quotes data from csv
        quotes_dict = dict()
        for x in quote_file_list:
            sym, quote = qc_csv_helper.file_to_quote_list(datapath + x,
                                                          markout_mode=MarkoutMode.Unhedged)
            quotes_dict[sym] = quote

        # now merge the quote and the trade list
        quote_trade_list = []
        for k, v in quotes_dict.items():
            # quote_async_iter = to_async_iterable(quotes_dict[k])
            # quote_trade_list.append(quote_async_iter)
            quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
            # trades_list_sym = []
            # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

            # trade_async_iter = to_async_iterable(trades_list_sym)
            quote_trade_list.append(quote_async_iter)

        quote_trade_list.append(trades_list)
        return quote_trade_list

    # Test for Sell in bps over intra-day to COB1
    def test_case_1(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)

        # Load the configuration file
        configurator = Configurator('config')
        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                t0 = time.time()
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                t1 = time.time()
                print("Time for data loading and merging: %s"%(t1-t0))
                output_list = []

                # run graph
                t0 = time.time()
                joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
                graph = joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) \
                        | op.flatten() > output_list
                run(graph)
                t1 = time.time()
                print("Time for running graph:%s" % (t1 - t0))

                # do assertions
                t0 = time.time()
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '0':
                        self.assertEquals(np.abs(mk_msg.bps_markout), 0.0, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-900':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.15)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-60':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.022) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '60':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0833)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '300':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.1333)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '3600':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.572)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0722)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.844)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                t1 = time.time()
                print("Time for running assertions:%s" % (t1 - t0))
        except Exception:
            raise Exception

    # Test for Sell in cents over intra-day to COB1
    def test_case_2(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        datapath = "../resources/unhedged_markout_tests/"
        quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        trade_files = "trades.csv"

        # create a singleton Configurator
        configurator = Configurator('config')
        try:
            with ExceptionLoggingContext():
                # Load the quotes data from csv
                logging.basicConfig(level=configurator.get_config_given_key('log_level'))
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
                    quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
                    # trades_list_sym = []
                    # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

                    # trade_async_iter = to_async_iterable(trades_list_sym)
                    quote_trade_list.append(quote_async_iter)
                    # quote_trade_list.append(trade_async_iter)

                output_list = []
                trade_async_iter = trades_list  # to_async_iterable(trades_list)
                quote_trade_list.append(trade_async_iter)
                joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
                graph = joint_stream | op.map_by_group(lambda x: x.sym,
                                                       GovtBondMarkoutCalculator()) | op.flatten() > output_list
                run(graph)
                # do assertions
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '0':
                        self.assertEquals(np.abs(mk_msg.cents_markout), 0.0, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '60':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - (-1.50)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '300':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - (-2.40)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '3600':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - (-10.30)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - (-1.30)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - (-15.20)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
        except Exception:
            raise Exception

    # Test for Buy in bps over intra-day to COB1
    def test_case_3(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        datapath = "../resources/unhedged_markout_tests/"
        quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        trade_files = "trades.csv"

        # Create a singleton configurator
        configurator = Configurator('config')
        try:
            with ExceptionLoggingContext():
                # Load the quotes data from csv
                logging.basicConfig(level=configurator.get_config_given_key('log_level'))
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
                    quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
                    # trades_list_sym = []
                    # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

                    # trade_async_iter = to_async_iterable(trades_list_sym)
                    quote_trade_list.append(quote_async_iter)
                    # quote_trade_list.append(trade_async_iter)

                output_list = []
                trade_async_iter = trades_list  # to_async_iterable(trades_list)
                quote_trade_list.append(trade_async_iter)
                joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
                graph = joint_stream | op.map_by_group(lambda x: x.sym,
                                                       GovtBondMarkoutCalculator()) | op.flatten() > output_list
                run(graph)
                # do assertions
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)

                for mk_msg in output_list:
                    if mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '0':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.38) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '60':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.47) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '300':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.51) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '3600':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.57) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.0722) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.844) / mk_msg.bps_markout),
                                             tolerance, msg=None)
        except Exception:
            raise Exception

    # Test for Buy in cents over intra-day to COB1
    def test_case_4(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        datapath = "../resources/unhedged_markout_tests/"
        quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        trade_files = "trades.csv"

        # Create a singleton configurator
        configurator = Configurator('config')
        try:
            with ExceptionLoggingContext():
                # Load the quotes data from csv
                logging.basicConfig(level=configurator.get_config_given_key('log_level'))
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
                    quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
                    # trades_list_sym = []
                    # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

                    # trade_async_iter = to_async_iterable(trades_list_sym)
                    quote_trade_list.append(quote_async_iter)
                    # quote_trade_list.append(trade_async_iter)

                output_list = []
                trade_async_iter = trades_list  # to_async_iterable(trades_list)
                quote_trade_list.append(trade_async_iter)
                joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
                graph = joint_stream | op.map_by_group(lambda x: x.sym,
                                                       GovtBondMarkoutCalculator()) | op.flatten() > output_list
                run(graph)
                # do assertions
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)

                for mk_msg in output_list:
                    if mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '0':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - 6.90) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '60':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - 8.40) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '300':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - 9.10) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == '3600':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - 10.20) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - 1.30) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.cents_markout - 15.20) / mk_msg.bps_markout),
                                             tolerance, msg=None)
        except Exception:
            raise Exception

    # ONLY COB markouts. Make sure the config file has only got COB0, COB1 and COB2 in lags_list
    def test_case_5(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        datapath = "../resources/unhedged_markout_tests/"
        quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        trade_files = "trades.csv"

        # Create a singleton configurator
        configurator = Configurator('config')
        try:
            with ExceptionLoggingContext():
                # Load the quotes data from csv
                logging.basicConfig(level=configurator.get_config_given_key('log_level'))
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
                    quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
                    # trades_list_sym = []
                    # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

                    # trade_async_iter = to_async_iterable(trades_list_sym)
                    quote_trade_list.append(quote_async_iter)
                    # quote_trade_list.append(trade_async_iter)

                output_list = []
                trade_async_iter = trades_list  # to_async_iterable(trades_list)
                quote_trade_list.append(trade_async_iter)
                joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
                graph = joint_stream | op.map_by_group(lambda x: x.sym,
                                                       GovtBondMarkoutCalculator(lags_list=['COB0', 'COB1', 'COB2'])) \
                        | op.flatten() > output_list
                run(graph)
                # do assertions
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
                self.assertEquals(len(output_list), 9, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.072) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.844) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "DE10YT_OTR_999" and mk_msg.dt == 'COB2':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-1.138)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "UST30Y_OTR_111111" and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-1.128)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "UST30Y_OTR_111111" and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-9.85)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "UST30Y_OTR_111111" and mk_msg.dt == 'COB2':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-13.41)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
        except Exception:
            raise Exception

    # test NaN
    def test_case_6(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        datapath = "../resources/unhedged_markout_tests/"
        quote_files = ["912810QE1_quotes.csv"]
        trade_files = "trades_NaN_test.csv"

        # Create a singleton configurator
        configurator = Configurator('config')

        try:
            with ExceptionLoggingContext():
                # Load the quotes data from csv
                logging.basicConfig(level=configurator.get_config_given_key('log_level'))
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
                    quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
                    # trades_list_sym = []
                    # [trades_list_sym.append(t) for t in trades_list if t.sym == k]

                    # trade_async_iter = to_async_iterable(trades_list_sym)
                    quote_trade_list.append(quote_async_iter)
                    # quote_trade_list.append(trade_async_iter)

                output_list = []
                trade_async_iter = trades_list  # to_async_iterable(trades_list)
                quote_trade_list.append(trade_async_iter)
                joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
                graph = joint_stream | op.map_by_group(lambda x: x.sym,
                                                       GovtBondMarkoutCalculator()) | op.flatten() > output_list
                run(graph)
                # do assertions
                self.assertEquals(len(output_list), 6, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == "222" and mk_msg.dt == '-900':
                        self.assertEquals(mk_msg.bps_markout, "NaN", msg=None)
                    elif mk_msg.trade_id == "222" and mk_msg.dt == '-60':
                        self.assertEquals(mk_msg.bps_markout, "NaN", msg=None)
                    elif mk_msg.trade_id == "222" and mk_msg.dt == '0':
                        self.assertEquals(mk_msg.bps_markout, 0.0, msg=None)
                    elif mk_msg.trade_id == "222" and mk_msg.dt == '60':
                        self.assertEquals(mk_msg.bps_markout, 0.0, msg=None)
                    elif mk_msg.trade_id == "222" and mk_msg.dt == '300':
                        self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.2439)) / mk_msg.bps_markout),
                                             tolerance, msg=None)
                    elif mk_msg.trade_id == "222" and mk_msg.dt == '3600':
                        self.assertLessEqual(np.abs(mk_msg.bps_markout - 0.4873) / mk_msg.bps_markout,
                                             tolerance, msg=None)
        except Exception:
            raise Exception

            # Test for Non-standard settlement trades
            # def test_case_7(self, plotFigure=False):
            #     tolerance = 5 * 1e-2
            #     thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
            #     os.chdir(thisfiledir)
            #     datapath = "../resources/unhedged_markout_tests/"
            #     quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
            #     trade_files = "trades_non_std.csv"
            #
            #     # Load the configuration file
            #     configurator = Configurator('config')
            #
            #     try:
            #         with ExceptionLoggingContext():
            #             # Load the quotes data from csv
            #             logging.basicConfig(level= configurator.get_config_given_key('log_level'))
            #             quotes_dict = dict()
            #             for x in quote_files:
            #                 sym, quote = qc_csv_helper.file_to_quote_list(datapath + x,
            #                                                               markout_mode=MarkoutMode.Unhedged)
            #                 quotes_dict[sym] = quote
            #
            #             # Now get the trades list from csv
            #             trades_list = qc_csv_helper.file_to_trade_list(datapath + trade_files)
            #
            #             # Method 2 - go through each of the instruments,
            #             # create a stream of quote per sym
            #             quote_trade_list = []
            #             for k, v in quotes_dict.items():
            #                 # quote_async_iter = to_async_iterable(quotes_dict[k])
            #                 # quote_trade_list.append(quote_async_iter)
            #                 quote_async_iter = to_async_iterable(quotes_dict[k])
            #                 # trades_list_sym = []
            #                 # [trades_list_sym.append(t) for t in trades_list if t.sym == k]
            #
            #                 # trade_async_iter = to_async_iterable(trades_list_sym)
            #                 quote_trade_list.append(quote_async_iter)
            #                 # quote_trade_list.append(trade_async_iter)
            #
            #             output_list = []
            #             trade_async_iter = to_async_iterable(trades_list)
            #             quote_trade_list.append(trade_async_iter)
            #             joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
            #             joint_stream | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) \
            #             | op.flatten() > output_list
            #
            #             # do assertions
            #             self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 1, msg=None)
            #             for mk_msg in output_list:
            #                 if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '0':
            #                     self.assertEquals(np.round(mk_msg.bps_markout, 3), 1.285, msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-900':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - 1.135) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-60':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - 1.307) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '60':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - 1.202) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '300':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - 1.151) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '3600':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.713) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB0':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0722)) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB1':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.844)) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #                 elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB2':
            #                     self.assertLessEqual(np.abs((mk_msg.bps_markout - 1.138) / mk_msg.bps_markout), tolerance,
            #                                          msg=None)
            #     except Exception:
            #         raise Exception
