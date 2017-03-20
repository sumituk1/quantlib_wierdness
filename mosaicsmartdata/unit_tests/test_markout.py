import aiostreams.operators.operators as op
from common import qc_csv_helper
from core.markout import GovtBondMarkoutCalculator
from aiostreams.base import to_async_iterable
from unittest import TestCase


class TestOrderBook(TestCase):
    # Test case for "Buy"
    def test_case_1(self, plotFigure = True):
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

        # Method 2 - go through each of of instruments,
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

        print(output_list)
