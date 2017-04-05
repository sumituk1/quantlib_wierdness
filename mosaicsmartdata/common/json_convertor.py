import csv
import datetime as dt
import numpy as np
from mosaicsmartdata.common.constants import *
from collections import namedtuple
import json
import operator
from mosaicsmartdata.core.instrument_singleton import *
from mosaicsmartdata.core.trade import Quote, FixedIncomeTrade

# Load instrument static
instrument_static = InstumentSingleton()


# converts a time precision in nano-seconds (kdb+) to a datetime object
def parse_iso_timestamp(timestamp):
    ts, partial_seconds = timestamp.rsplit('.', 1)
    partial_seconds = float("." + partial_seconds)
    time = dt.datetime.strptime(ts, "%Y.%m.%dD%H:%M:%S")
    precise_datetime = time + dt.timedelta(seconds=partial_seconds)
    return precise_datetime


# Convert json message to FixedIncomeTrade object
def json_to_trade(json_message):
    request = json.loads(json_message, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
    tr = FixedIncomeTrade(trade_id=request.bondTrade.negotiationId,
                          sym=request.bondTrade.sym,
                          notional=request.bondTrade.quantity,
                          timestamp=parse_iso_timestamp(request.bondTrade.timestamp),
                          is_benchmark=True if request.bondTrade.issueOldness else False,
                          side=TradeSide.Ask if str.upper(request.bondTrade.side) == "ASK" else TradeSide.Bid,
                          traded_px=float(request.bondTrade.tradedPx),
                          client_sys_key=None,
                          package_id=request.bondTrade.packageId,
                          tenor=float(request.bondTrade.tenor),
                          trade_date=dt.datetime.strptime(request.bondTrade.tradeDate, "%Y.%m.%d"),
                          ccy=request.bondTrade.ccy,
                          trade_settle_date=dt.datetime.strptime(request.bondTrade.settlementDate, "%Y.%m.%d"),
                          spot_settle_date=dt.datetime.strptime(request.bondTrade.spotSettlementDate, "%Y.%m.%d"),
                          venue=request.bondTrade.venue,
                          duration=float(request.bondTrade.modifiedDuration))
    return tr


# Converts a markout message to a json string
def mktmsg_to_json(markout_message):
    # "negotiationId": "ID123456789",
    #   "instrumentId": "1234567",
    #   "dateLocalDate": "2017-01-01",
    #   "cashflowDirection": "+",
    #   "venueName": "venueNameValue",
    #   "legMarkout": {
    #     "evaluatedPricingSourceDimensionItem": {
    #       "evaluatedPricingSource": "INTERNAL",
    #       "description": "Internal"
    #     },
    #     "markoutPeriodDimensionItem": {
    #       "markoutPeriod": {
    #         "timeUnit": "DAYS",
    #         "value": 1
    #       }
    #     },
    #     "markoutPrice": {
    #       "priceType": {
    #         "priceType": "UNHEDGED_INITIAL_EDGE"
    #       },
    #       "value": 0.98765
    #     }
    #   }
    out = dict()
    out['negotiationId'] = markout_message.trade.trade_id
    out['instrumentId'] = markout_message.trade.sym
    out['dateLocalDate'] = dt.datetime.strftime(markout_message.trade.trade_date, '%Y-%m-%d')
    out['cashflowDirection'] = "+" if markout_message.trade.side == TradeSide.Bid else "-"
    out['venueName'] = markout_message.trade.venue
    out['legMarkout'] = []

    # dict_evaluatedPricingSource = {'evaluatedPricingSource': 'INTERNAL'}
    # out['legMarkout'].append({'evaluatedPricingSource': 'INTERNAL'})
    # out['legMarkout']['evaluatedPricingSourceDimensionItem']['description'] = 'Internal'
    dict_markoutPeriod = {}
    if "COB" not in str(markout_message.dt):
        dict_markoutPeriod['timeUnit'] = 'SECONDS'
        dict_markoutPeriod['value'] = markout_message.dt
    elif "COB" in str(markout_message.dt):
        dict_markoutPeriod['timeUnit'] = 'DAY'
        dict_markoutPeriod['value'] = markout_message.dt[-1]

    # set the UNHEDGED price/cents/bps
    # --------------------------------
    lst_markoutPrice = []
    attribs = [a for a in dir(markout_message) if not a.startswith('__') and 'markout' in a]
    mk_type = attribs[0][:-8]
    mults = markout_message.trade.markout_mults()
    if mk_type in mults:
        for key, value in mults.items():
            if key == 'bps':
                val = markout_message.price_markout * value \
                    if markout_message.price_markout is not None else np.nan
                lst_markoutPrice.append({'priceType': 'UNHEDGED_INITIAL_EDGE', 'value': val})
                # out['legMarkout']['markoutPrice'].append({'value' : val})
            if key == 'cents':
                val = markout_message.price_markout * value \
                    if markout_message.price_markout is not None else np.nan
                lst_markoutPrice.append({'priceType': 'UNHEDGED_SPREAD_PRICE', 'value': val})
    # set the HEDGED price/cents/bps
    # --------------------------------
    val = markout_message.hedged_bps if markout_message.hedged_bps is not None else np.nan
    lst_markoutPrice.append({'priceType': 'HEDGED_INITIAL_EDGE', 'value': val})

    val = markout_message.hedged_cents if markout_message.hedged_cents is not None else np.nan
    lst_markoutPrice.append({'priceType': 'HEDGED_SPREAD_PRICE', 'value': val})

    out['legMarkout'].append({'evaluatedPricingSource': 'INTERNAL',
                              "markoutPeriod": dict_markoutPeriod,
                              "markoutPrice": lst_markoutPrice})
    # out['legMarkout']['markoutPrice'] = lst
    zz = json.dumps(out)
    return zz


# Create a Quote object based on incoming json message
def json_to_quote(json_message):
    request = json.loads(json_message, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
    # calculate a vwap of bids
    zz = [[float(x.entrySize), float(x.entryPx)] for x in request[0][0].marketDataEntryList if
          str.upper(x.entryType) == "BID"]
    bid_close = sum([x[0] * x[1] for x in zz]) / sum([x[0] for x in zz])
    # calculate a vwap of ask
    zz = [[float(x.entrySize), float(x.entryPx)] for x in request[0][0].marketDataEntryList if
          str.upper(x.entryType) == "OFFER"]
    ask_close = sum([x[0] * x[1] for x in zz]) / sum([x[0] for x in zz])
    quote = Quote(sym=request[0][0].symbol,
                  ask=ask_close,
                  timestamp=dt.datetime.fromtimestamp(request[0][0].timestamp / 1000),
                  bid=bid_close)
    return quote


if __name__ == "__main__":
    json_message = '{"bondTrade": {"negotiationId": "123456789", "orderId": "123456789::venue::date::DE10YT_OTR_111::BUY",\
                   "packageId": "123456789::venue::date", "productClass": "GovtBond", "productClass1": "DE10YT",\
                   "sym": "DE10YT=RR", "tenor": 30, "quantity": 114.235, "tradedPx": 1.5, "modifiedDuration": 18.0,\
                   "side": "Ask", "quantityDv01": 18.0, "issueOldness": 1,"ccy": "USD", ' \
                   '"timestamp": "2017.01.16D14:05:00.600000000",\
                   "tradeDate": "2017.01.16", "settlementDate": "2017.01.18", "holidayCalendar": "NYC",\
                   "spotSettlementDate": "2017.01.18", "venue": "BBGUST"}}'

    print(json_to_trade(json_message=json_message))

    msg = '{\
      "marketDataSnapshotFullRefreshList": [\
        {\
          "securityId": "CUSIP",\
          "symbol": "912810RB6",\
          "timestamp": 1485941760000,\
          "marketDataEntryList": [\
            {\
              "entryId": "entryId101",\
              "entryType": "BID",\
              "entryPx": "1.1243",\
              "currencyCode": "USD",\
              "settlementCurrencyCode": "USD",\
              "entrySize": "1000000",\
              "quoteEntryId": "quoteEntryId101"\
            },\
            {\
              "entryId": "entryId102",\
              "entryType": "MID",\
              "entryPx": "1.12345",\
              "currencyCode": "USD",\
              "settlementCurrencyCode": "USD",\
              "entrySize": "1000000",\
              "quoteEntryId": "quoteEntryId102"\
            },\
            {\
              "entryId": "entryId103",\
              "entryType": "OFFER",\
              "entryPx": "1.1246",\
              "currencyCode": "USD",\
              "settlementCurrencyCode": "USD",\
              "entrySize": "1000000",\
              "quoteEntryId": "quoteEntryId103"\
            },\
            {\
              "entryId": "entryId201",\
              "entryType": "BID",\
              "entryPx": "1.12445",\
              "currencyCode": "USD",\
              "settlementCurrencyCode": "USD",\
              "entrySize": "500000",\
              "quoteEntryId": "quoteEntryId201"\
            },\
            {\
              "entryId": "entryId202",\
              "entryType": "MID",\
              "entryPx": "1.12345",\
              "currencyCode": "USD",\
              "settlementCurrencyCode": "USD",\
              "entrySize": "500000",\
              "quoteEntryId": "quoteEntryId202"\
            },\
            {\
              "entryId": "entryId203",\
              "entryType": "OFFER",\
              "entryPx": "1.12445",\
              "currencyCode": "USD",\
              "settlementCurrencyCode": "USD",\
              "entrySize": "500000",\
              "quoteEntryId": "quoteEntryId203"\
            }\
          ]\
        }\
      ]\
    }'

    quote = json_to_quote(msg)
    print(quote)
