import importlib
import logging

importlib.reload(logging)
# logging.basicConfig(level = logging.INFO)
from unittest import TestCase
import numpy as np
import math
import asyncio
import random
import aiostreams.operators as op
from aiostreams import run, ExceptionLoggingContext, AsyncKafkaPublisher, AsyncKafkaSource
from aiostreams import KafkaPersister
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.common.read_config import Configurator
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.core.markout import GovtBondMarkoutCalculator
import time
import datetime as dt
from mosaicsmartdata.common.test_utils import read_quotes_trades
from mosaicsmartdata.core.quote import Quote
from mosaicsmartdata.core.trade import Trade,FixedIncomeTrade
from mosaicsmartdata.core.markout_basket_builder import *
from mosaicsmartdata.core.pca_risk import *
from mosaicsmartdata.common.json_convertor import *
import os, inspect
from aiostreams.main import main_function
thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
os.chdir(thisfiledir)


class TestMarkouts(TestCase):
    # def setUp(self):
        # self.config = QCConfigProvider()

    # function to read the quotes and trade file and merge them to a iterable list

    def json_merge_quotes_trade(self, json_trade, json_quote):
        quote_trade_list = []
        quote_list = []
        trade_list = []
        trade = json_to_trade(json_message=json_trade)
        trade_list.append(trade)
        quote = json_to_quote(json_message=json_quote)
        quote_list.append(quote)
        # quote_dict[quote.sym] = quote
        quote_trade_list.append(trade_list)
        quote_trade_list.append(quote_list)
        return quote_trade_list

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
            quote_async_iter = quotes_dict[k]  # to_async_iterable(quotes_dict[k])
            quote_trade_list.append(quote_async_iter)

        quote_trade_list.append(trades_list)
        return quote_trade_list

    # create the graph
    def create_graph(self, quote_trade_list):
        output_list = []
        # run graph
        # t0 = time.time()
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        graph_1 = joint_stream | op.map(PCARisk())| op.flatten() | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator())| op.flatten()

        graph_2 = graph_1 | op.map_by_group(lambda x: (x.trade_id, x.dt), PackageBuilder()) \
                            | op.flatten() | op.map(aggregate_multi_leg_markouts) | \
                            op.map_by_group(lambda x: x.package_id, AllMarkoutFilter()) | op.flatten() > output_list

        return graph_2,output_list

    # create the graph
    def create_graph_2(self, quote_trade_list):
        output_list = []
        # run graph
        # t0 = time.time()
        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        graph_1 = joint_stream | op.map(PCARisk()) | op.flatten() | op.map_by_group(lambda x: x.sym,
                                                                                    GovtBondMarkoutCalculator()) | op.flatten()

        graph_2 = graph_1 | op.map_by_group(lambda x: (x.trade_id, x.dt), PackageBuilder()) \
                  | op.flatten() | op.map(aggregate_multi_leg_markouts) | op.map(domain_to_json) > output_list

        return graph_2, output_list

    # runs the graph and returns the output_list
    def run_graph_2(self, quote_trade_list):
        graph,output_list = self.create_graph_2(quote_trade_list)
        run(graph)
        return output_list

    # runs the graph and returns the output_list
    def run_graph(self, quote_trade_list):
        graph,output_list = self.create_graph(quote_trade_list)
        run(graph)
        return output_list

    # Test for Sell in bps over intra-day to COB1
    def test_case_1(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)

        # Load the configuration file
        configurator = Configurator('config.csv')
        # try:
        if True:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
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

        # except ValueError:# Exception:
        #     raise Exception

    # Test case 1 but with a "Filter" for the last trade
    def test_case_1b(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)

        # Load the configuration file
        configurator = Configurator('config.csv')
        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(
                    datapath="../resources/unhedged_markout_tests/",
                    quote_file_list=["912810RB6_quotes.csv",
                                     "DE10YT_RR_quotes.csv",
                                     "US30YT_RR_quotes.csv"],
                    trade_file="trades_filter.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
                # self.assertEquals(len(output_list), 27, msg=None)
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
                self.assertEquals(len(output_list), 27, msg=None)
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

        except ValueError:  # Exception:
            raise Exception

    # Test for Sell in cents over intra-day to COB1
    def test_case_2(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)

        # create a singleton Configurator
        configurator = Configurator('config.csv')
        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)
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
        # datapath = "../resources/unhedged_markout_tests/"
        # quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        # trade_files = "trades.csv"

        # Create a singleton configurator
        configurator = Configurator('config.csv')
        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

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
        t0 = time.time()
        # datapath = "../resources/unhedged_markout_tests/"
        # quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        # trade_files = "trades.csv"

        # Create a singleton configurator
        configurator = Configurator('config.csv')
        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

                print("time taken=%s"%(time.time()-t0))
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
        t0 = time.time()
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        # datapath = "../resources/unhedged_markout_tests/"
        # quote_files = ["912810RB6_quotes.csv", "DE10YT_RR_quotes.csv", "US30YT_RR_quotes.csv"]
        # trade_files = "trades.csv"

        # Create a singleton configurator
        configurator = Configurator('config.csv')
        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

                print("time taken=%s" % (time.time() - t0))

                # do assertions
                self.assertEquals(len(set([(lambda x: x.trade_id)(x) for x in output_list])), 3, msg=None)
                self.assertEquals(len(output_list), 9*3, msg=None)
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

    # Same as test_case_5. But uses a Kafka Persistence every COB
    def test_case_6(self, plotFigure=False):
        t0 = time.time()
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        logging.getLogger().setLevel('INFO')
        logging.getLogger().info("test")
        # Create a singleton configurator
        configurator = Configurator('config.csv')
        #try:
        with ExceptionLoggingContext():
            # load the trade and quote data and merge
            quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                quote_file_list=["912810RB6_quotes.csv",
                                                                                 "DE10YT_RR_quotes.csv",
                                                                                 "US30YT_RR_quotes.csv"],
                                                                trade_file="trades.csv")
            graph,output_list = self.create_graph(quote_trade_list)
            graph.id = 'my_nice_graph_3'

            # create a pp
            class pp:
                def __init__(self):
                    self.last_date_persisted = None
                    self.COB_time_utc_eur = \
                        configurator.get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
                    self.COB_time_utc_ust = \
                        configurator.get_data_given_section_and_key("GovtBond_Markout", "UST_COB")
                    self.COB_time_utc_gbp = \
                        configurator.get_data_given_section_and_key("GovtBond_Markout", "GBP_COB")
                    self.num_calls = 0
                # implement a COB persist policy
                # def __init__(self, cob_ts):
                #     self.cob = cob_ts
                #     self.last_timestamp = None

                def __call__(self, msg):
                    # get the COB time per ccy
                    if msg.trade.ccy == Currency.EUR:
                        self.COB_time_utc = self.COB_time_utc_eur
                    elif msg.trade.ccy == Currency.USD:
                        self.COB_time_utc = self.COB_time_utc_ust
                    elif msg.trade.ccy == Currency.GBP:
                        self.COB_time_utc = self.COB_time_utc_gbp
                    # now convert the str_time to time object
                    self.COB_time_utc = dt.datetime.strptime(self.COB_time_utc, "%H:%M:%S").time()
                    if msg.timestamp.time() > self.COB_time_utc:
                        # only make one snapshot per day
                        if not (self.last_date_persisted == msg.timestamp.date()):
                            self.last_date_persisted = msg.timestamp.date()
                            print('COB!!!', msg.timestamp)
                            self.num_calls += 1
                            # only snapshot the first 2 COBs so the reflated graph still has days to run
                            if self.num_calls < 3:
                                print('persisting...')
                                return True
                        else:
                            print(msg.timestamp)
                        return False

            graph.persistence_policy = pp()
            # run the graph
            run(graph)
            #run(asyncio.sleep(1))
            output_list = graph.sink
            print('inital run completed')

        with ExceptionLoggingContext():
            print('starting load attempt')
            # run(asyncio.sleep(1)) # so Kafka has time to propagate
            loaded = KafkaPersister().load('my_nice_graph_3')
            print(loaded.last_msg.timestamp)
            run(loaded)
            #print(loaded.sink)
            self.assertEqual(graph.sink, loaded.sink)

    # test NaN
    def test_case_7(self, plotFigure=False):
        t0 = time.time()
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)
        # datapath = "../resources/unhedged_markout_tests/"
        # quote_files = ["912810QE1_quotes.csv"]
        # trade_files = "trades_NaN_test.csv"

        # Create a singleton configurator
        configurator = Configurator('config.csv')

        try:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810QE1_quotes.csv"],
                                                                    trade_file="trades_NaN_test.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

                print("time taken=%s" % (time.time() - t0))
                # do assertions
                self.assertEquals(len(output_list), 6, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == "222" and mk_msg.dt == '-900':
                        self.assertTrue(math.isnan(mk_msg.bps_markout), msg=None)
                    elif mk_msg.trade_id == "222" and mk_msg.dt == '-60':
                        self.assertTrue(math.isnan(mk_msg.bps_markout), msg=None)
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

    # Repeat for Test-Case 1 but testing the domain_to_json
    def test_case_8(self, plotFigure=False):
        tolerance = 5 * 1e-2
        thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        os.chdir(thisfiledir)

        # Load the configuration file
        configurator = Configurator('config.csv')
        # try:
        if True:
            with ExceptionLoggingContext():
                # load the trade and quote data and merge
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/unhedged_markout_tests/",
                                                                    quote_file_list=["912810RB6_quotes.csv",
                                                                                     "DE10YT_RR_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv"],
                                                                    trade_file="trades.csv")
                # run the graph
                output_list = self.run_graph_2(quote_trade_list)

                # do assertions
                if output_list[0].find("DE10YT_OTR_111")!= -1:
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": -900") != -1:
                        ## pre 900 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.15)) / x),tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": -900") != -1:
                        ## pre 900 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.15)) / x), tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": 0") != -1:
                        ## POT markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertEquals(np.abs(x), 0, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": -60") != -1:
                        ## pre 60 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - 0.022) / x), tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": 60") != -1:
                        ## post 60 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.0833)) / x), tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": 300") != -1:
                        ## post 300 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.1333)) / x), tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": 3600") != -1:
                        ## post 3600 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.572)) / x), tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": COB0") != -1:
                        ## post COB0 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.0722)) / x), tolerance, msg=None)
                    if output_list[0].find("\"timeUnit\": \"SECONDS\",\"value\": COB1") != -1:
                        ## post COB1 secs markout in bps
                        x = output_list[0][output_list[0].find("UNHEDGED_INITIAL_EDGE") + 33:
                        output_list[0].find("UNHEDGED_INITIAL_EDGE") + 40]
                        self.assertLessEqual(np.abs((x - (-0.844)) / x), tolerance, msg=None)

                #
                # for mk_msg in output_list:
                #     if mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '0':
                #         self.assertEquals(np.abs(mk_msg.bps_markout), 0.0, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-900':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.15)) / mk_msg.bps_markout),
                #                              tolerance, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '-60':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - 0.022) / mk_msg.bps_markout),
                #                              tolerance, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '60':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0833)) / mk_msg.bps_markout),
                #                              tolerance, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '300':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.1333)) / mk_msg.bps_markout),
                #                              tolerance, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == '3600':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.572)) / mk_msg.bps_markout),
                #                              tolerance, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB0':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.0722)) / mk_msg.bps_markout),
                #                              tolerance, msg=None)
                #     elif mk_msg.trade_id == "DE10YT_OTR_111" and mk_msg.dt == 'COB1':
                #         self.assertLessEqual(np.abs((mk_msg.bps_markout - (-0.844)) / mk_msg.bps_markout),
                #                              tolerance, msg=None)

        # except ValueError:# Exception:
        #     raise Exception

if __name__ == '__main__':
    #    unittest.main()
    k= TestMarkouts()
    k.setUp()
    k.test_case_6()
