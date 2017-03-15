import csv
from core.trade import Quote, Trade,FixedIncomeTrade
import datetime as dt
from core.constants import *


# Create a Quote object by reading data from csv.
# In the future, this will come from Kafka
def file_to_quote_list(fname):
    with open(fname, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    # convert them to Quote objects, assuming first row is headers

    quote = [Quote(instr=x[3], ask=x[2],
                    timestamp=dt.datetime.strptime(x[0], "%d/%m/%Y %H:%M"),
                    bid=x[1]) for x in my_list[1:]]
    # make sure they're sorted in ascending order
    quote = sorted(quote, key=lambda x: x.timestamp)

    return quote[0].instr, quote


# Create a Trade object by reading data from csv.
# In the future, this will come from Kafka
def file_to_trade_list(fname):
    trade_list = []
    with open(fname, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    # convert them to Trade objects, assuming first row is headers
    for x in my_list[1:]:
        tr = Trade()
        tr.trade_id = x[1]
        tr.sym = x[4]
        tr.notional = float(x[6])
        tr.timestamp = dt.datetime.strptime(x[13], "%d/%m/%Y %H:%M")
        tr.side = TradeSide.Ask if x[10] == "Ask" else TradeSide.Bid
        tr.traded_px = float(x[7])
        # tr.mid_px = 96.935
        tr.client_key = x[17]
        tr.duration = float(x[9])
        # tr.on_repo = 0.02
        tr.trade_date = x[14]
        tr.traded_px = float(x[7])
        tr.ccy = 'EUR'
        # tr.calculate_trade_dv01()
        trade_list.append(tr)
    return trade_list