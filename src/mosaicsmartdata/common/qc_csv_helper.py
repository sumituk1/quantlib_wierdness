import csv
import datetime as dt
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.core.instrument_static_singleton import *
from mosaicsmartdata.core.trade import *
from mosaicsmartdata.core.quote import Quote
from mosaicsmartdata.core.instrument_utils import sym_to_instrument

def indfun(headers, string):
    return [i for i, name in enumerate(headers) if string in name][0]

def reuters_to_datetime(rdate, rtime):
    ts, partial_seconds = rtime.split('.')
    partial_seconds = float("." + partial_seconds)
    time = dt.datetime.strptime(rdate + '-' + ts, "%d-%b-%Y-%H:%M:%S")
    precise_datetime = time + dt.timedelta(seconds=partial_seconds)
    return precise_datetime

def get_ric_quotes(filename):
    headers = None
    quote_dict = {}
    instr_gen = sym_to_instrument()
    with open(filename) as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for i,row in enumerate(spamreader):
            if not headers:
                headers = row
                ricind = indfun(headers, 'RIC')
                dateind = indfun(headers, 'Date')
                timeind = indfun(headers, 'Time')
                bidind = indfun(headers, 'Bid Price')
                askind = indfun(headers, 'Ask Price')
            else:
                sym = row[ricind]
                timestamp = reuters_to_datetime(row[dateind],row[timeind])
                bid = row[bidind]
                ask = row[askind]
                try:
                    bid = float(bid)
                    ask = float(ask)
                    quote = Quote(sym = sym,
                                  timestamp = timestamp,
                                  bid = bid,
                                  ask = ask)
                    quote.instrument = instr_gen(sym, timestamp.date())
                    if 'OIS' in sym:
                        quote.units = 'percent'
                    elif quote.instrument.tenor == 'SPOT': # assume FX if not OIS
                        quote.units = 'outright'
                    else:
                        quote.units = 'pips'

                    if i%100000 == 0:
                        print(i, quote)
                    if sym not in quote_dict:
                        quote_dict[sym] = []
                    quote_dict[sym].append(quote)
                except:
                    pass # ignore malformed quote rows
        print(i,quote)
    return quote_dict

# converts a time precision in nano-seconds (kdb+) to a datetime object
def parse_iso_timestamp(timestamp):
    ts, partial_seconds = timestamp.rsplit('.', 1)
    partial_seconds = float("." + partial_seconds)
    time = dt.datetime.strptime(ts, "%Y.%m.%dD%H:%M:%S")
    precise_datetime = time + dt.timedelta(seconds=partial_seconds)
    return precise_datetime


# Create a Quote object by reading data from csv.
# In the future, this will come from Kafka
def file_to_quote_list(fname, markout_mode=MarkoutMode.Unhedged):
    # Load instrument static
    configurator = Configurator()
    instrument_static = InstrumentStaticSingleton()

    with open(fname, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    # for simple markouts, we don;t need the duration in the Quotes
    quote = [Quote(sym=x[3],
                   ask=float(x[2]),
                   timestamp=parse_iso_timestamp(x[0]),
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
        tr = FixedIncomeBondTrade(trade_id=x[1],
                                  sym=x[4],
                                  notional=float(x[6]),
                                  timestamp=parse_iso_timestamp(x[13]),
                                  side=TradeSide.Ask if x[10] == "Ask" else TradeSide.Bid,
                                  traded_px=float(x[7]),
                                  client_sys_key=x[16],
                                  tenor=float(x[5]),
                                  trade_date=dt.datetime.strptime(x[14], "%Y.%m.%d"),
                                  ccy=x[18],
                                  trade_settle_date=dt.datetime.strptime(x[15], "%Y.%m.%d"),
                                  spot_settle_date=dt.datetime.strptime(x[26], "%Y.%m.%d"),
                                  maturity_date=dt.datetime.strptime(x[19], "%Y.%m.%d"),
                                  coupon=float(x[20]),
                                  holidayCities=x[21],
                                  coupon_frequency=Frequency.convertFrequencyStr(x[22]),
                                  day_count=DayCountConv.convertDayCountStr(x[24]),
                                  issue_date=dt.datetime.strptime(x[25], "%Y.%m.%d") if x[25] != "" else None,
                                  duration=float(x[9]),
                                  country_of_risk=x[27],
                                  price_type=PriceType.convert_price_type(x[30]) if x[30] != "" else None)
        trade_list.append(tr)
    return trade_list


# Create a Trade object by reading data from csv.
# In the future, this will come from Kafka
def file_to_swaps_trade_list(fname):
    trade_list = []
    with open(fname, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    # convert them to Trade objects, assuming first row is headers
    for x in my_list[1:]:
        tr = InterestRateSwapTrade(trade_id=x[1],
                                   sym=x[4],
                                   notional=float(x[6]),  # mandatory notional
                                   timestamp=parse_iso_timestamp(x[13]),
                                   side=TradeSide.Ask if x[10] == "Ask" else TradeSide.Bid,
                                   traded_px=float(x[7]),  # has to have a traded_px
                                   client_sys_key=x[16],
                                   tenor=float(x[5]),  # has to have a tenor
                                   trade_date=dt.datetime.strptime(x[14], "%Y.%m.%d"),
                                   ccy=x[18],
                                   trade_settle_date=dt.datetime.strptime(x[15], "%Y.%m.%d"),
                                   spot_settle_date=dt.datetime.strptime(x[26], "%Y.%m.%d"),
                                   maturity_date=dt.datetime.strptime(x[19], "%Y.%m.%d"),
                                   coupon=float(x[20]) if x[20] != "" else None,  # optional coupon
                                   holidayCities=x[21],
                                   coupon_frequency=Frequency.convertFrequencyStr(x[22]),
                                   float_coupon_frequency=Frequency.convertFrequencyStr(x[23]),
                                   day_count=DayCountConv.convertDayCountStr(x[24]),
                                   issue_date=dt.datetime.strptime(x[25], "%Y.%m.%d") if x[25] != "" else None,
                                   duration=float(x[9]),  # mandatory duration
                                   country_of_risk=x[27],
                                   orig_package_size=float(x[28]),
                                   leg_no=float(x[29]),
                                   price_type=PriceType.convert_price_type(x[30]) if x[30] != "" else None,
                                   rfqdeal_upfront_fee=float(x[31]) if len(my_list[0]) > 31 and x[31] != "" else 0.0
                                   )
        trade_list.append(tr)
    return trade_list


if __name__ == "__main__":
    ts = "2017.03.21D11:19:45.605345678"
    zz = parse_iso_timestamp(ts)
    print(type(zz))
