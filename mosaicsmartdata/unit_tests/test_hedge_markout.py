from __future__ import absolute_import
from unittest import TestCase
import numpy as np
import seaborn as sns
import datetime as dt
import matplotlib.pyplot as plt
import aiostreams.operators.operators as op
from aiostreams.base import to_async_iterable
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.core.markout import GovtBondMarkoutCalculator
from mosaicsmartdata.core.markout_basket_builder import *
from mosaicsmartdata.core.hedger import *


class TestHedgeMarkouts(TestCase):
    # Test hedge with Cash
    def test_case_1(self, plotFigure=False):
        tolerance = 5 * 1e-2
        datapath = "..\\resources\\hedged_markout_tests\\"  # generally a good idea to use relative paths whenever possible
        quote_files = ["912828T91_quotes.csv", "US30YT_RR_quotes.csv", "US10YT_RR_quotes.csv", "US5YT_RR_quotes.csv"]
        trade_files = "trades_hedge_test.csv"

        # Create a singleton configurator and instrument_static
        configurator = Configurator('config')
        instrument_static = InstumentSingleton()

        # Load the quotes data from csv
        quotes_dict = dict()
        for x in quote_files:
            sym, quote = qc_csv_helper.file_to_quote_list(datapath + x, MarkoutMode.Hedged)
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
        hedger = Hedger(my_hedge_calculator, product_class=ProductClass.GovtBond)

        # 1. set up initla hedges at point of trade
        new_trades = joint_stream | op.map(hedger) | op.flatten()
        # 2. Perform markouts of both underlying trade and the paper_trades
        leg_markout = new_trades | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten()
        # 3. Aggregate all the markouts per package_id
        leg_markout | op.map_by_group(lambda x: (x.package_id, x.dt), MarkoutBasketBuilder()) | op.flatten() | \
        op.map(aggregate_markouts) > output_list

        # do assertions
        self.assertEquals(len(output_list), 9, msg=None)
        for mk_msg in output_list:
            if mk_msg.trade_id == 456 and mk_msg.dt == '-900':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents), tolerance, msg=None)
            if mk_msg.trade_id == 456 and mk_msg.dt == '-60':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents), tolerance, msg=None)
            if mk_msg.trade_id == 456 and mk_msg.dt == '0':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02394) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.7125) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.09277) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 1.10313) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.01609) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 5.4) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.19828)) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 41.3375) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.49894)) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 46.4156) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB2':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.42919)) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 37.8219) / mk_msg.hedged_cents), tolerance, msg=None)
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

    # Test hedge with futures
    def test_case_2(self, plotFigure=False):
        tolerance = 5 * 1e-2
        datapath = "..\\resources\\hedged_markout_tests\\"
        quote_files = ["912828T91_quotes.csv",
                       "FVc1_quotes.csv","TUc1_quotes.csv","TYc1_quotes.csv","USc1_quotes.csv"]
        trade_files = "trades_hedge_test.csv"

        # Create a singleton configurator
        configurator = Configurator('config')
        instrument_static = InstumentSingleton()

        # Load the quotes data from csv
        quotes_dict = dict()
        for x in quote_files:
            sym, quote = qc_csv_helper.file_to_quote_list(datapath + x, MarkoutMode.Hedged)
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
        hedger = Hedger(my_hedge_calculator) # <- No need to pass in Futures specifically, as thats the first be default

        # 1. set up initla hedges at point of trade
        new_trades = joint_stream | op.map(hedger) | op.flatten()
        # 2. Perform markouts of both underlying trade and the paper_trades
        leg_markout = new_trades | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten()
        # 3. Aggregate all the markouts per package_id
        leg_markout | op.map_by_group(lambda x: (x.package_id, x.dt), MarkoutBasketBuilder()) | op.flatten() | \
        op.map(aggregate_markouts) > output_list

        # do assertions
        self.assertEquals(len(output_list), 9, msg=None)
        for mk_msg in output_list:
            if mk_msg.trade_id == 456 and mk_msg.dt == '-900':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.25344)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-2.4125)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            if mk_msg.trade_id == 456 and mk_msg.dt == '-60':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.26105)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-3.1937)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            if mk_msg.trade_id == 456 and mk_msg.dt == '0':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.26105)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-3.1937)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.2648)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-3.584)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.0771)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-2.021)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.6263)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-9.834)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-6.7429)) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-76.631)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 4.0339) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-11.787)) / mk_msg.hedged_cents), tolerance,
                                     msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB2':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 8.359) / mk_msg.hedged_bps), tolerance,
                                     msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 22.196) / mk_msg.hedged_cents), tolerance,
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

    # Test case for betas using 2 Cash hedge instruments
    def test_case_3(self):
        trade_duration = 6.159
        hedge_quote_sym = 'US5YT=RR'
        hedge_sym_arr = ['US5YT=RR', 'US10YT=RR']
        lastquotes = {'912828T91':Quote(sym='912828T91',
                                        ask=96.4921875,
                                        timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                        bid=96.46875,
                                        duration=6.159),
                      'US5YT=RR':Quote(sym='US5YT=RR',
                                       ask=96.4921875,
                                       timestamp=dt.datetime(2017, 3, 24, 22, 0, 0),
                                       bid=96.46875,
                                       duration=4.672),
                      'US10YT=RR':Quote(sym='US10YT=RR',
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

    # Test hedge where a 7y has got a 10yr and 30yr specified as a hedge (Enable config_2.txt)
    # Code should pick up the first one i.e. 10yr
    def test_case_5(self, plotFigure=True):
        tolerance = 5 * 1e-2
        datapath = "..\\resources\\hedged_markout_tests\\"
        quote_files = ["912828T91_quotes.csv", "US30YT_RR_quotes.csv", "US10YT_RR_quotes.csv", "US5YT_RR_quotes.csv"]
        trade_files = "trades_hedge_test.csv"

        # Create a singleton configurator
        configurator = Configurator('config_hedge_test_case_5')
        instrument_static = InstumentSingleton()

        # Load the quotes data from csv
        quotes_dict = dict()
        for x in quote_files:
            sym, quote = qc_csv_helper.file_to_quote_list(datapath + x, MarkoutMode.Hedged)
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
        hedger = Hedger(my_hedge_calculator, product_class=ProductClass.GovtBond)

        # 1. set up initla hedges at point of trade
        new_trades = joint_stream | op.map(hedger) | op.flatten()
        # 2. Perform markouts of both underlying trade and the paper_trades
        leg_markout = new_trades | op.map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator()) | op.flatten()
        # 3. Aggregate all the markouts per package_id
        leg_markout | op.map_by_group(lambda x: (x.package_id, x.dt), MarkoutBasketBuilder()) | op.flatten() | \
        op.map(aggregate_markouts) > output_list

        # do assertions
        self.assertEquals(len(output_list), 9, msg=None)
        for mk_msg in output_list:
            if mk_msg.trade_id == 456 and mk_msg.dt == '-900':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.0266) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance, msg=None)
            if mk_msg.trade_id == 456 and mk_msg.dt == '-60':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02661) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents -(-0.0687)) / mk_msg.hedged_cents), tolerance, msg=None)
            if mk_msg.trade_id == 456 and mk_msg.dt == '0':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02661) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '60':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.02661) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-0.0687)) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '300':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.0900) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - 0.3218) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == '3600':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - 0.07512) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-1.6312)) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB0':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.5031)) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-21.9437)) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB1':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.9256)) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-27.8031)) / mk_msg.hedged_cents), tolerance, msg=None)
            elif mk_msg.trade_id == 456 and mk_msg.dt == 'COB2':
                self.assertLessEqual(np.abs((mk_msg.hedged_bps - (-0.8957)) / mk_msg.hedged_bps), tolerance, msg=None)
                self.assertLessEqual(np.abs((mk_msg.hedged_cents - (-23.896)) / mk_msg.hedged_cents), tolerance, msg=None)
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