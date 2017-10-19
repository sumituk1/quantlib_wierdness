import logging
import importlib
#importlib.reload(logging)
# logging.basicConfig(level = logging.INFO)
#from aiostreams.base import EventLoopContext
from aiostreams import run,ExceptionLoggingContext
import time
from unittest import TestCase
import numpy as np
# import seaborn as sns
import datetime as dt
try: # matplotlib install on Docker turned out to be nontrivial, and we don't need it there anyway
    import matplotlib.pyplot as plt
except:
    pass
import aiostreams.operators as op
#from aiostreams.base import to_async_iterable
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.core.markout import GovtBondMarkoutCalculator
from mosaicsmartdata.core.markout_basket_builder import *
from mosaicsmartdata.core.hedger import *
from mosaicsmartdata.core.pca_risk import *
import os, inspect
from mosaicsmartdata.common.json_convertor import *
from mosaicsmartdata.core.historical_markouts import *

thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
os.chdir(thisfiledir)


class TestHedgeMarkouts(TestCase):
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

    # runs the graph and returns the output_list
    def run_graph(self, quote_trade_list, product_class = ProductClass.GovtBond.value):
        output_list = []

        joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        hedger = Hedger(my_hedge_calculator, product_class=product_class)
        def get_legs(x):
            try:
                return copy(x.legs)
            except:
                return [x]

        # 1. set up initial hedges at point of trade
        new_trades = joint_stream | op.map_by_group(lambda x: x.package_id , PackageBuilder()) |\
                        op.flatten() | op.map(hedger) | op.flat_map(get_legs)

        leg_markout = new_trades | op.map(PCARisk()) | op.flatten() | \
                      op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten()

        # 2. Aggregate all the markouts per package_id
        leg_markout_final = leg_markout | op.map_by_group(lambda x: (x.trade_id, x.dt), PackageBuilder()) \
                            | op.flatten() | op.map(aggregate_multi_leg_markouts) | \
                            op.map_by_group(lambda x: x.package_id, AllMarkoutFilter()) | op.flatten() > output_list

        # # 2. Perform markouts of both underlying trade and the paper_trades
        # leg_markout = new_trades | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten()
        # # 3. Aggregate all the markouts per package_id
        # leg_markout_final = leg_markout | op.map_by_group(lambda x: (x.package_id, x.dt),
        #                                                   PackageBuilder()) | op.flatten() | \
        #                     op.map(aggregate_markouts) > output_list
        # run the pipe
        run(leg_markout_final)
        return output_list

    # create graph for historical
    def run_graph_historical(self, trade_quote_tuple,product_class = ProductClass.GovtBond.value):
        output_list = []
        quote_trade_list = []
        # hedger = Hedger(my_hedge_calculator, product_class=product_class)

        def get_legs(x):
            try:
                return copy(x.legs)
            except:
                return [x]
        # 1. set up initial hedges at point of trade
        new_trades = [trade_quote_tuple] | op.map(historical_hedge_package_builder)| op.flatten() \
                     | op.flat_map(get_legs)

        # run(new_trades)
        # joint_stream = op.merge_sorted(quote_trade_list, lambda x: x.timestamp)
        leg_markout = new_trades | op.map(PCARisk()) | op.flatten() | \
                      op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten()

        # run(leg_markout)
        # 2. Aggregate all the markouts per package_id
        leg_markout_final = leg_markout | op.map_by_group(lambda x: (x.trade_id, x.dt), PackageBuilder()) \
                              | op.flatten() | op.map(aggregate_multi_leg_markouts) | \
                              op.map_by_group(lambda x: x.package_id, AllMarkoutFilter()) | op.flatten() > output_list
        run(leg_markout_final)

        return output_list
    # Test hedge with Cash
    def test_case_1(self, plotFigure=False):
        tolerance = 5 * 1e-2
        t0 = time.time()
        # Create a singleton configurator and instrument_static
        configurator = Configurator('config.csv')
        instrument_static = InstrumentStaticSingleton() # required for hedge instrument duration

        #try:
        if True:
            with ExceptionLoggingContext():

                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/hedged_markout_tests/",
                                                                    quote_file_list=["912828T91_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv",
                                                                                     "US10YT_RR_quotes.csv",
                                                                                     "US5YT_RR_quotes.csv"],
                                                                    trade_file="trades_hedge_test.csv")

                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
                self.assertEquals(len(output_list), 9, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == '456' and mk_msg.dt == '-900':
                        self.assertAlmostEqual(mk_msg.hedged_bps,0.030,3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459,3)
                    if mk_msg.trade_id == '456' and mk_msg.dt == '-60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    if mk_msg.trade_id == '456' and mk_msg.dt == '0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '300':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.094, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.069, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '3600':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.000, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -5.928, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.115, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -52.803, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB1':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.382, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -63.350, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB2':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.301, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -52.412, 3)

                print("Time taken: %s"%(time.time() - t0))
                # plot figure
                if plotFigure:
                    fig, ax = plt.subplots()
                    x_data = [x.dt for x in output_list]

                    plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
                    plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
                    ax.set_xticklabels(x_data)
                    plt.xlabel("time")
                    plt.ylabel("markout(bps)")
                    plt.legend()
                    plt.grid(True)
                    plt.show()
        # except Exception:
        #     raise Exception
        #     pass

    # Test case 1 but second trade will be filtered out i.e. test filter on hedging pipeline
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
                    datapath="../resources/hedged_markout_tests/",
                    quote_file_list=["912828T91_quotes.csv",
                                     "US30YT_RR_quotes.csv",
                                     "US10YT_RR_quotes.csv",
                                     "US5YT_RR_quotes.csv"],
                    trade_file="trades_hedge_test_filter.csv")
                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
                # do assertions
                self.assertEquals(len(output_list), 9, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == '456' and mk_msg.dt == '-900':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    if mk_msg.trade_id == '456' and mk_msg.dt == '-60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    if mk_msg.trade_id == '456' and mk_msg.dt == '0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.030, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.459, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '300':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.094, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -0.069, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '3600':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.000, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -5.928, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.115, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -52.803, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB1':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.382, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -63.350, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB2':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.301, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -52.412, 3)

        except ValueError:  # Exception:
            raise Exception

    # Test hedge with futures
    def test_case_2(self, plotFigure=False):
        tolerance = 5 * 1e-2
        t0 = time.time()

        # Create a singleton configurator
        configurator = Configurator('config.csv')
        instrument_static = InstrumentStaticSingleton()

        #try:
        if True:
            with ExceptionLoggingContext():
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/hedged_markout_tests/",
                                                                    quote_file_list=["912828T91_quotes.csv",
                                                                                     "FVc1_quotes.csv",
                                                                                     "TUc1_quotes.csv",
                                                                                     "TYc1_quotes.csv",
                                                                                     "USc1_quotes.csv"],
                                                                    trade_file="trades_hedge_test.csv")

                # run the graph
                output_list = self.run_graph(quote_trade_list,ProductClass.BondFutures.value)

                # do assertions
                self.assertEquals(len(output_list), 9, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == '456' and mk_msg.dt == '-900':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.253, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -2.412, 3)
                    if mk_msg.trade_id == '456' and mk_msg.dt == '-60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.261, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -3.194, 3)
                    if mk_msg.trade_id == '456' and mk_msg.dt == '0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.261, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -3.194, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.265, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -3.584, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '300':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.0771, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -2.022, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == '3600':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.626, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -9.834, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -6.743, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -76.631, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB1':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 4.034, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, -11.787, 3)
                    elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB2':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 8.359, 3)
                        self.assertAlmostEquals(mk_msg.hedged_cents, 22.197, 3)

                print("Time elapsed=%s"%(time.time()-t0))
                # plot figure
                if plotFigure:
                    fig, ax = plt.subplots()
                    x_data = [x.dt for x in output_list]

                    plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
                    plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
                    ax.set_xticklabels(x_data)
                    plt.xlabel("time")
                    plt.ylabel("markout(bps)")
                    plt.legend()
                    plt.grid(True)
                    plt.show()
        # except Exception:
        #     raise Exception
        #     pass

    # Test case for betas using 2 Cash hedge instruments
    def test_case_3(self):
        trade_duration = 6.159
        hedge_quote_sym = 'US5YT=RR'
        hedge_sym_arr = ['US5YT=RR', 'US10YT=RR']
        lastquotes = {'912828T91': Quote(sym='912828T91',
                                         ask=96.4921875,
                                         timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                         bid=96.46875,
                                         duration=6.159),
                      'US5YT=RR': Quote(sym='US5YT=RR',
                                        ask=96.4921875,
                                        timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                        bid=96.46875,
                                        duration=4.672),
                      'US10YT=RR': Quote(sym='US10YT=RR',
                                         ask=96.4921875,
                                         timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                         bid=96.46875,
                                         duration=8.771)}

        beta = extract_beta(hedge_quote_sym, trade_duration, hedge_sym_arr, lastquotes)
        self.assertEquals(np.round(beta, 3), 0.637, msg=None)
        hedge_quote_sym = 'US10YT=RR'
        beta = extract_beta(hedge_quote_sym, trade_duration, hedge_sym_arr, lastquotes)
        self.assertEquals(np.round(beta, 3), 0.363, msg=None)

    # Test case for betas using 2 Futures hedge instruments
    def test_case_4(self):
        trade_duration = 6.159
        hedge_quote_sym = 'FVc1'
        hedge_sym_arr = ['FVc1', 'TYc1']
        lastquotes = {'912828T91': Quote(sym='912828T91',
                                         ask=96.4921875,
                                         timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                         bid=96.46875,
                                         duration=6.159),
                      'FVc1': Quote(sym='FVc1',
                                    ask=96.4921875,
                                    timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                    bid=96.46875,
                                    duration=4.265),
                      'TYc1': Quote(sym='TYc1',
                                    ask=96.4921875,
                                    timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                    bid=96.46875,
                                    duration=6.230)}

        beta = extract_beta(hedge_quote_sym, trade_duration, hedge_sym_arr, lastquotes)
        self.assertEquals(np.round(beta, 3), 0.036, msg=None)
        hedge_quote_sym = 'TYc1'
        beta = extract_beta(hedge_quote_sym, trade_duration, hedge_sym_arr, lastquotes)
        self.assertEquals(np.round(beta, 3), 0.964, msg=None)

    # Test hedge where a 7y has got a 10yr and 30yr specified as a hedge (Enable config_hedge_test_case_5)
    # Code should pick up the first one i.e. 10yr
    def test_case_5(self, plotFigure=False):
        tolerance = 5 * 1e-2
        # datapath = "../resources/hedged_markout_tests/"
        # quote_files = ["912828T91_quotes.csv", "US30YT_RR_quotes.csv", "US10YT_RR_quotes.csv", "US5YT_RR_quotes.csv"]
        # trade_files = "trades_hedge_test.csv"

        # Create a singleton configurator
        configurator = Configurator('config_hedge_test_case_5')
        instrument_static = InstrumentStaticSingleton()

        try:
            with ExceptionLoggingContext():
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/hedged_markout_tests/",
                                                                    quote_file_list=["912828T91_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv",
                                                                                     "US10YT_RR_quotes.csv",
                                                                                     "US5YT_RR_quotes.csv"],
                                                                    trade_file="trades_hedge_test.csv")

                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
                self.assertEquals(len(output_list), 9, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == 456 and mk_msg.dt == '-900':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.0266) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    if mk_msg.trade_id == 456 and mk_msg.dt == '-60':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02661) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    if mk_msg.trade_id == 456 and mk_msg.dt == '0':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02661) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    elif mk_msg.trade_id == 456 and mk_msg.dt == '60':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02661) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    elif mk_msg.trade_id == 456 and mk_msg.dt == '300':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.0900) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.3218) / mk_msg.hedged_cents), tolerance, msg=None)
                    elif mk_msg.trade_id == 456 and mk_msg.dt == '3600':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.07512) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-1.6312)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB0':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.5031)) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-21.9437)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB1':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.9256)) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-27.8031)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                    elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB2':
                        self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.8957)) / mk_msg.hedged_bps), tolerance, msg=None)
                        self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-23.896)) / mk_msg.hedged_cents), tolerance,
                                             msg=None)
                # plot figure
                if plotFigure:
                    fig, ax = plt.subplots()
                    x_data = [x.dt for x in output_list]

                    plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
                    plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
                    ax.set_xticklabels(x_data)
                    plt.xlabel("time")
                    plt.ylabel("markout(bps)")
                    plt.legend()
                    plt.grid(True)
                    plt.show()
        except Exception:
            raise Exception
            pass

    # test BTP hedging rule
    def test_case_6(self, plotFigure=False):
        tolerance = 5 * 1e-2
        # datapath = "../resources/hedged_markout_tests/"
        # quote_files = ["912828T91_quotes.csv", "US30YT_RR_quotes.csv", "US10YT_RR_quotes.csv", "US5YT_RR_quotes.csv",
        #                "IT488903_quotes.csv", "IT15YT_RR_quotes.csv", "IT30YT_RR_quotes.csv", "FBTPc1_RR_quotes.csv"]
        # trade_files = "trades_hedge_test_2.csv"

        # Create a singleton configurator
        configurator = Configurator('config.csv')
        instrument_static = InstrumentStaticSingleton()

        try:
            with ExceptionLoggingContext():
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/hedged_markout_tests/",
                                                                    quote_file_list=["912828T91_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv",
                                                                                     "US10YT_RR_quotes.csv",
                                                                                     "US5YT_RR_quotes.csv",
                                                                                     "IT488903_quotes.csv",
                                                                                     "IT15YT_RR_quotes.csv",
                                                                                     "IT30YT_RR_quotes.csv",
                                                                                     "FBTPc1_RR_quotes.csv"],
                                                                    trade_file="trades_hedge_test_2.csv")

                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
                self.assertEquals(len(output_list), 9, msg=None)
                for mk_msg in output_list:
                    if mk_msg.trade_id == '123' and mk_msg.dt == '-900':
                        self.assertAlmostEqual(mk_msg.hedged_bps,0.283,3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, 2.299,3)
                    if mk_msg.trade_id == '123' and mk_msg.dt == '-60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.064, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, -0.825, 3)
                    if mk_msg.trade_id == '123' and mk_msg.dt == '0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.064, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, -0.825, 3)
                    elif mk_msg.trade_id == '123' and mk_msg.dt == '60':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.064, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, -0.825, 3)
                    elif mk_msg.trade_id == '123' and mk_msg.dt == '300':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.168, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, 1.519, 3)
                    elif mk_msg.trade_id == '123' and mk_msg.dt == '3600':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.290, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, 3.862, 3)
                    elif mk_msg.trade_id == '123' and mk_msg.dt == 'COB0':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -0.001, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, 0.737, 3)
                    elif mk_msg.trade_id == '123' and mk_msg.dt == 'COB1':
                        self.assertAlmostEqual(mk_msg.hedged_bps, -1.472, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, -18.013, 3)
                    elif mk_msg.trade_id == '123' and mk_msg.dt == 'COB2':
                        self.assertAlmostEqual(mk_msg.hedged_bps, 0.905, 3)
                        self.assertAlmostEqual(mk_msg.hedged_cents, 5.425, 3)
                # plot figure
                if plotFigure:
                    fig, ax = plt.subplots()
                    x_data = [x.dt for x in output_list]

                    plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
                    plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
                    ax.set_xticklabels(x_data)
                    plt.xlabel("time")
                    plt.ylabel("markout(bps)")
                    plt.legend()
                    plt.grid(True)
                    plt.show()
        except Exception:
            raise Exception

    # test BTP Cash hedging rule
    def test_case_7(self, plotFigure=False):
        tolerance = 5 * 1e-2
        t0 = time.time()
        # datapath = "../resources/hedged_markout_tests/"
        # quote_files = ["912828T91_quotes.csv", "US30YT_RR_quotes.csv", "US10YT_RR_quotes.csv",
        #                "US5YT_RR_quotes.csv",
        #                "IT488903_quotes.csv", "IT15YT_RR_quotes.csv", "IT30YT_RR_quotes.csv",
        #                "FBTPc1_RR_quotes.csv"]
        # trade_files = "trades_hedge_test_2.csv"

        # Create a singleton configurator
        configurator = Configurator('config.csv')
        instrument_static = InstrumentStaticSingleton()

        try:
            with ExceptionLoggingContext():
                quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/hedged_markout_tests/",
                                                                    quote_file_list=["912828T91_quotes.csv",
                                                                                     "US30YT_RR_quotes.csv",
                                                                                     "US10YT_RR_quotes.csv",
                                                                                     "US5YT_RR_quotes.csv",
                                                                                     "IT488903_quotes.csv",
                                                                                     "IT15YT_RR_quotes.csv",
                                                                                     "IT30YT_RR_quotes.csv",
                                                                                     "FBTPc1_RR_quotes.csv"],
                                                                    trade_file="trades_hedge_test_2.csv")

                # run the graph
                output_list = self.run_graph(quote_trade_list)

                # do assertions
                self.assertEquals(len(output_list), 9, msg=None)
                print("Time elapsed = %s"%(time.time()-t0))
                # for mk_msg in output_list:
                #     if mk_msg.trade_id == 123 and mk_msg.dt == '-900':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.869) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - 6.981) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     if mk_msg.trade_id == 123 and mk_msg.dt == '-60':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.2522) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - 1.85625) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     if mk_msg.trade_id == 123 and mk_msg.dt == '0':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.01837) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.1437)) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     elif mk_msg.trade_id == 123 and mk_msg.dt == '60':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.01837)) / mk_msg.hedged_bps), tolerance,
                #                              msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.1437)) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     elif mk_msg.trade_id == 123 and mk_msg.dt == '300':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.2901) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - 2.4187) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     elif mk_msg.trade_id == 123 and mk_msg.dt == '3600':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - -0.01837) / mk_msg.hedged_bps), tolerance,
                #                              msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.1437)) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     elif mk_msg.trade_id == 123 and mk_msg.dt == 'COB0':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 3.3260) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - 24.29374) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     elif mk_msg.trade_id == 123 and mk_msg.dt == 'COB1':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 8.429) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - 61.7312) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)
                #     elif mk_msg.trade_id == 123 and mk_msg.dt == 'COB2':
                #         self.assertLessEqual(np.abs((mk_msg.hedged_bps - 12.9047) / mk_msg.hedged_bps), tolerance, msg=None)
                #         self.assertLessEqual(np.abs((mk_msg.hedged_cents - 97.9187) / mk_msg.hedged_cents), tolerance,
                #                              msg=None)

                # plot figure
                if plotFigure:
                    fig, ax = plt.subplots()
                    x_data = [x.dt for x in output_list]

                    plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
                    plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
                    ax.set_xticklabels(x_data)
                    plt.xlabel("time")
                    plt.ylabel("markout(bps)")
                    plt.legend()
                    plt.grid(True)
                    plt.show()
        except Exception:
            raise Exception

    # Test hedge with Cash historical
    def test_case_8(self, plotFigure=False):
        tolerance = 5 * 1e-2
        t0 = time.time()
        # Create a singleton configurator and instrument_static
        configurator = Configurator('config.csv')
        instrument_static = InstrumentStaticSingleton()  # required for hedge instrument duration

        json_message = '{\
            "bondTrade": {\
              "negotiationId": "456",\
              "orderId": "456::venue::date::DE10YT_OTR_111::BUY",\
              "packageId": "DE10YT_OTR_111::venue::date",\
              "productClass": "GovtBond",\
              "productClass1": "GT7",\
              "sym": "912828T91",\
              "tenor": 7,\
              "quantity": 10000000,\
              "tradedPx": 96.071,\
              "modifiedDuration": 6.159,\
              "side": "BID",\
              "quantityDv01": 6159,\
              "issueOldness": 1,\
              "timestamp": "2017.03.21D11:19:45.605000000",\
              "tradeDate": "2017.03.21",\
              "settlementDate": "2017.03.22",\
              "holidayCalendar": "EUR",\
              "spotSettlementDate": "2017.03.22",\
              "venue": "BBGUST",\
              "ccy": "USD",\
              "countryOfIssue": "US",\
              "dayCount": "ACT\/ACT",\
              "issueDate": "2015.04.16",\
              "coupon": 2,\
              "couponFrequency": "ANNUAL",\
              "maturityDate": "2022.04.16",\
              "midPrices": [\
                {\
                  "timestamp": 1490094286000,\
                  "entryType": "MID",\
                  "entryPx": 96.078125,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490095126000,\
                  "entryType": "MID",\
                  "entryPx": 96.078125,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490095186000,\
                  "entryType": "MID",\
                  "entryPx": 96.078125,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490095246000,\
                  "entryType": "MID",\
                  "entryPx": 96.078125,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490095486000,\
                  "entryType": "MID",\
                  "entryPx": 96.08203125,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490098786000,\
                  "entryType": "MID",\
                  "entryPx": 96.125,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490133600000,\
                  "entryType": "MID",\
                  "entryPx": 96.484375,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490220000000,\
                  "entryType": "MID",\
                  "entryPx": 96.53515625,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490306400000,\
                  "entryType": "MID",\
                  "entryPx": 96.44921875,\
                  "sym":"912828T91"\
                },\
                {\
                  "timestamp": 1490094286000,\
                  "entryType": "MID",\
                  "entryPx": 97.8984375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490095126000,\
                  "entryType": "MID",\
                  "entryPx": 97.8984375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490095186000,\
                  "entryType": "MID",\
                  "entryPx": 97.8984375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490095246000,\
                  "entryType": "MID",\
                  "entryPx": 97.8984375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490095486000,\
                  "entryType": "MID",\
                  "entryPx": 97.8984375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490098786000,\
                  "entryType": "MID",\
                  "entryPx": 97.9609375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490133600000,\
                  "entryType": "MID",\
                  "entryPx": 98.5234375,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490220000000,\
                  "entryType": "MID",\
                  "entryPx": 98.6328125,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490306400000,\
                  "entryType": "MID",\
                  "entryPx": 98.5078125,\
                  "sym":"US10YT=RR"\
                },\
                {\
                  "timestamp": 1490094286000,\
                  "entryType": "MID",\
                  "entryPx": 99.35546875,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490095126000,\
                  "entryType": "MID",\
                  "entryPx": 99.35546875,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490095186000,\
                  "entryType": "MID",\
                  "entryPx": 99.35546875,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490095246000,\
                  "entryType": "MID",\
                  "entryPx": 99.35546875,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490095486000,\
                  "entryType": "MID",\
                  "entryPx": 99.35546875,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490098786000,\
                  "entryType": "MID",\
                  "entryPx": 99.39453125,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490133600000,\
                  "entryType": "MID",\
                  "entryPx": 99.66015625,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490220000000,\
                  "entryType": "MID",\
                  "entryPx": 99.70703125,\
                  "sym":"US5YT=RR"\
                },\
                {\
                  "timestamp": 1490306400000,\
                  "entryType": "MID",\
                  "entryPx": 99.63671875,\
                  "sym":"US5YT=RR"\
                }\
              ]\
            }\
          }'

        trade, quote_list = json_to_domain(json_message=json_message, historical=True)
        # run the graph
        output_list = self.run_graph_historical(tuple((trade, quote_list)))

        # do assertions
        self.assertEquals(len(output_list), 8, msg=None)
        for mk_msg in output_list:
            # if mk_msg.trade_id == '456' and mk_msg.dt == '-900':
            #     self.assertEqual(mk_msg.hedged_bps, np.nan)
            #     self.assertEqual(mk_msg.hedged_cents, np.nan)
            if mk_msg.trade_id == '456' and mk_msg.dt == '-60':
                self.assertAlmostEqual(mk_msg.hedged_bps, 0.114,3)
                self.assertAlmostEquals(mk_msg.hedged_cents, 0.692,3)
            if mk_msg.trade_id == '456' and mk_msg.dt == '0':
                self.assertAlmostEqual(mk_msg.hedged_bps, 0.114, 3)
                self.assertAlmostEquals(mk_msg.hedged_cents, 0.692, 3)
            elif mk_msg.trade_id == '456' and mk_msg.dt == '60':
                self.assertAlmostEqual(mk_msg.hedged_bps, 0.114, 3)
                self.assertAlmostEquals(mk_msg.hedged_cents, 0.692, 3)
            elif mk_msg.trade_id == '456' and mk_msg.dt == '300':
                self.assertAlmostEqual(mk_msg.hedged_bps, 0.114, 3)
                self.assertAlmostEquals(mk_msg.hedged_cents, 0.692, 3)
            elif mk_msg.trade_id == '456' and mk_msg.dt == '3600':
                self.assertAlmostEqual(mk_msg.hedged_bps, 0.177, 3)
                self.assertAlmostEquals(mk_msg.hedged_cents, 1.083, 3)
            elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB0':
                self.assertAlmostEqual(mk_msg.hedged_bps, -0.031, 3)
                self.assertAlmostEquals(mk_msg.hedged_cents, -51.651, 3)
            elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB1':
                self.assertAlmostEqual(mk_msg.hedged_bps, -0.298, 3)
                self.assertAlmostEquals(mk_msg.hedged_cents, -62.198, 3)
            # elif mk_msg.trade_id == '456' and mk_msg.dt == 'COB2':
            #     self.assertAlmostEqual(mk_msg.hedged_bps, 0.114, 3)
            #     self.assertAlmostEquals(mk_msg.hedged_cents, 0.692, 3)

        print("Time taken: %s" % (time.time() - t0))
        # plot figure
        if plotFigure:
            fig, ax = plt.subplots()
            x_data = [x.dt for x in output_list]

            plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
            plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
            ax.set_xticklabels(x_data)
            plt.xlabel("time")
            plt.ylabel("markout(bps)")
            plt.legend()
            plt.grid(True)
            plt.show()
                    # except Exception:
                    #     raise Exception
                    #     pass


        # # try:
        # if True:
        #     with ExceptionLoggingContext():
        #
        #         quote_trade_list = self.read_and_merge_quotes_trade(datapath="../resources/hedged_markout_tests/",
        #                                                             quote_file_list=["912828T91_quotes.csv",
        #                                                                              "US30YT_RR_quotes.csv",
        #                                                                              "US10YT_RR_quotes.csv",
        #                                                                              "US5YT_RR_quotes.csv"],
        #                                                             trade_file="trades_hedge_test.csv")
        #
        #         # run the graph
        #         output_list = self.run_graph(quote_trade_list)
        #
        #         # do assertions
        #         self.assertEquals(len(output_list), 9, msg=None)
        #         for mk_msg in output_list:
        #             if mk_msg.trade_id == 456 and mk_msg.dt == '-900':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance,
        #                                      msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             if mk_msg.trade_id == 456 and mk_msg.dt == '-60':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance,
        #                                      msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             if mk_msg.trade_id == 456 and mk_msg.dt == '0':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance,
        #                                      msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             elif mk_msg.trade_id == 456 and mk_msg.dt == '60':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance,
        #                                      msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             elif mk_msg.trade_id == 456 and mk_msg.dt == '300':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.09277) / mk_msg.hedged_bps), tolerance,
        #                                      msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 1.10313) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             elif mk_msg.trade_id == 456 and mk_msg.dt == '3600':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.01609) / mk_msg.hedged_bps), tolerance,
        #                                      msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 5.4) / mk_msg.hedged_cents), tolerance,
        #                                      msg=None)
        #             elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB0':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.19828)) / mk_msg.hedged_bps),
        #                                      tolerance, msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 41.3375) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB1':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.49894)) / mk_msg.hedged_bps),
        #                                      tolerance, msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 46.4156) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #             elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB2':
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.42919)) / mk_msg.hedged_bps),
        #                                      tolerance, msg=None)
        #                 self.assertLessEqual(np.abs((mk_msg.hedged_cents - 37.8219) / mk_msg.hedged_cents),
        #                                      tolerance, msg=None)
        #
        #         print("Time taken: %s" % (time.time() - t0))
        #         # plot figure
        #         if plotFigure:
        #             fig, ax = plt.subplots()
        #             x_data = [x.dt for x in output_list]
        #
        #             plt.plot([x.hedged_bps for x in output_list], label="hedged markout_bps", color="red")
        #             plt.plot([x.bps_markout for x in output_list], label="unhedged markout_bps", color="blue")
        #             ax.set_xticklabels(x_data)
        #             plt.xlabel("time")
        #             plt.ylabel("markout(bps)")
        #             plt.legend()
        #             plt.grid(True)
        #             plt.show()
        #             # except Exception:
        #             #     raise Exception
        #             #     pass

if __name__ == '__main__':
    #    unittest.main()
    k= TestHedgeMarkouts()
    #k.setUp()
    k.test_case_2()