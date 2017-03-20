import csv
import datetime as dt
from mosaicsmartdata.core.trade import Quote, Trade, FixedIncomeTrade
from mosaicsmartdata.core.constants import *


# Create a Quote object by reading data from csv.
# In the future, this will come from Kafka
def file_to_quote_list(fname):
    with open(fname, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    # convert them to Quote objects, assuming first row is headers

    quote = [Quote(sym=x[3],
                   ask=float(x[2]),
                   timestamp=dt.datetime.strptime(x[0], "%Y.%m.%dD%H:%M:%S"),
                   bid=float(x[1])) for x in my_list[1:]]
    # make sure they're sorted in ascending order
    quote = sorted(quote, key=lambda x: x.timestamp)

    return quote[0].sym, quote


# Create a Trade object by reading data from csv.
# In the future, this will come from Kafka
def file_to_trade_list(fname):
    trade_list = []
    with open(fname, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    # convert them to Trade objects, assuming first row is headers
    for x in my_list[1:]:
        tr = FixedIncomeTrade( trade_id=x[1],
                               sym=x[4],
                               notional=float(x[6]),
                               timestamp=dt.datetime.strptime(x[13], "%Y.%m.%dD%H:%M:%S"),
                               side=TradeSide.Ask if x[10] == "Ask" else TradeSide.Bid,
                               traded_px=float(x[7]),
                               client_sys_key=x[17],
                               trade_date=dt.datetime.strptime(x[14], "%Y.%m.%d"),
                               ccy=x[18],
                               trade_settle_date=dt.datetime.strptime(x[15], "%Y.%m.%d"),
                               duration=float(x[9]))
        trade_list.append(tr)
    return trade_list
