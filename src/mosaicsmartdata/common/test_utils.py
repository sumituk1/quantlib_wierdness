from aiostreams import operators as op
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.common.constants import MarkoutMode


def read_quotes_trades(datapath, quote_file_list, trade_file):
    # get the trades list from csv
    trades = qc_csv_helper.file_to_trade_list(datapath + trade_file)

    # Load the quotes data from csv
    quotes = []
    for x in quote_file_list:
        sym, quote = qc_csv_helper.file_to_quote_list(datapath + x,
                                                      markout_mode=MarkoutMode.Unhedged)
        quotes.append(quote)

    joint_quotes = op.merge_sorted(quotes, lambda x: x.timestamp)

    return joint_quotes, trades