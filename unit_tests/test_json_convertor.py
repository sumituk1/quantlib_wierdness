from unittest import TestCase
from mosaicsmartdata.core.markout_msg import MarkoutMessage2
from mosaicsmartdata.common.json_convertor import *


class TestMarkouts(TestCase):
    # Test for Trade json convertor
    def test_case_1(self):
        json_message = '{"bondTrade": {"negotiationId": "123456789", "orderId": "123456789::venue::date::DE10YT_OTR_111::BUY",\
            "packageId": "123456789::venue::date", "productClass": "GovtBond", "productClass1": "DE10YT",\
            "sym": "DE10YT=RR", "tenor": 30, "quantity": 1000000, "tradedPx": 1.5, "modifiedDuration": 18.0,\
            "side": "Ask", "quantityDv01": 1800.0, "issueOldness": 1,"ccy": "USD", ' \
           '"timestamp": "2017.01.16D14:05:00.600000000",\
           "tradeDate": "2017.01.16", "settlementDate": "2017.01.18", "holidayCalendar": "NYC",\
           "spotSettlementDate": "2017.01.18", "venue": "BBGUST","countryOfIssue": "US","dayCount": "ACT/ACT",' \
           '"issueDate": "2016.10.31","coupon": 1.2,"couponFrequency": "ANNUAL","maturityDate": "2047.01.18"}}'
        trade = json_to_trade(json_message=json_message)

        # do assertions
        self.assertEquals(trade.duration, 18, msg=None)
        self.assertEquals(trade.delta, 1800, msg=None)
        self.assertEquals(trade.trade_date, dt.datetime(2017,1,16), msg=None)
        self.assertEquals(trade.notional, 1000000, msg=None)
        self.assertEquals(trade.traded_px, 1.5, msg=None)
        self.assertEquals(trade.venue, "BBGUST", msg=None)
        self.assertEquals(trade.side, TradeSide.Ask, msg=None)
        self.assertEquals(trade.timestamp, dt.datetime(2017,1,16,14,5,0,600000), msg=None)

        return trade

    # Test for Quote json convertor
    def test_case_2(self):
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

        # do assertions
        self.assertEquals(quote.timestamp, dt.datetime(2017,2,1,9,36,00), msg=None)
        self.assertEquals(quote.ask, 1.12455, msg=None)
        self.assertEquals(quote.bid, 1.12435, msg=None)
        self.assertEquals(quote.sym, '912810RB6', msg=None)

    # test case for json creation for mkt_message
    def test_case_3(self):
        trade = self.test_case_1()
        # t = FixedIncomeTrade(trade_id=1, duration=20, notional=5)

        msg = MarkoutMessage2(dt=-900,trade=trade, price_markout=1, hedged_bps=0.34, hedged_cents=0.13, hedged_price=1.05)

        # do assertions on the markout_message
        self.assertEqual(round(msg.bps_markout,3), 5.556)
        self.assertEqual(msg.cents_markout, 100.0)
        self.assertEqual(msg.PV_markout, 1800)
        self.assertEqual(msg.price_markout, 1)

        json_markout = mktmsg_to_json(msg)
        print(json_markout) # check if the markoutPeriod value = -900

    # test case for json creation for mkt_message
    def test_case_4(self):
        trade = self.test_case_1()
        # t = FixedIncomeTrade(trade_id=1, duration=20, notional=5)

        msg = MarkoutMessage2(dt='COB2', trade=trade, price_markout=1, hedged_bps=0.34, hedged_cents=0.13,
                              hedged_price=1.05)

        # do assertions on the markout_message
        self.assertEqual(round(msg.bps_markout, 3), 5.556)
        self.assertEqual(msg.cents_markout, 100.0)
        self.assertEqual(msg.PV_markout, 1800)
        self.assertEqual(msg.price_markout, 1)

        json_markout = mktmsg_to_json(msg)

        print("json_markout") # CHECK IF THE MARKOUTPERIODVALUE = 0AND TIMEUNIT='DAY'
