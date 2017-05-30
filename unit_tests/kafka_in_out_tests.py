'''
To start Kafka 9 in Docker (using image from https://hub.docker.com/r/flozano/kafka/) run the following in the Docker bash:
  docker run -p 2181:2181 -p 9092:9092 --env _KAFKA_advertised_host_name=`docker-machine ip \`docker-machine active\`` --env _KAFKA_advertised_port=9092 --name=local_kafka flozano/kafka &
To kill it run
  docker kill local_kafka
then
  docker rm local_kafka
'''
import importlib
import logging

importlib.reload(logging)
logging.basicConfig(level=logging.ERROR)
from aiostreams import ExceptionLoggingContext, run, AsyncKafkaPublisher
from unittest import TestCase
from kafka import KafkaProducer, KafkaConsumer
from aiostreams.kafka_utils import AsyncKafkaSource
import aiostreams.operators as op
from aiostreams.config import QCConfigProvider
from mosaicsmartdata.common.json_convertor import *
from mosaicsmartdata.core.markout_msg import MarkoutMessage2

kafka_host = QCConfigProvider().kafka_broker  # Kafka on local Docker

class TestKafka(TestCase):
    # Dump a json object into kafka and then read back and convert to Trade object
    def test_case_1(self, plotFigure=False):
        tolerance = 5 * 1e-2
        json_message_in = '{"bondTrade": {"negotiationId": "123456789", "orderId": ' \
                          '"123456789::venue::date::DE10YT_OTR_111::BUY","packageId": ' \
                          '"123456789::venue::date", "productClass": "GovtBond", "productClass1": "DE10YT",' \
                          '"sym": "DE10YT=RR", "tenor": 30, "quantity": 1000000, "tradedPx": 1.5, ' \
                          '"modifiedDuration": 18.0,"side": "Bid", "quantityDv01": 18.0, ' \
                          '"issueOldness": 1,"timestamp": "2017.01.16D14:05:00.600000000",' \
                          '"tradeDate": "2017.01.16", "settlementDate": "2017.01.24", ' \
                          '"holidayCalendar": "NYC","spotSettlementDate": "2017.01.18","ccy": ' \
                          '"USD","countryOfIssue": "US","dayCount": "ACT/ACT","issueDate": "2016.10.31",' \
                          '"coupon": 1.2,"couponFrequency": "ANNUAL","maturityDate": "2047.01.18","venue": "BBGUST"}}'
        # Load the configuration file
        configurator = Configurator('config')
        logging.basicConfig(level=configurator.get_config_given_key('log_level'))
        try:
            with ExceptionLoggingContext():

                topic = 'trade_sub_1'
                topic2 = 'quote_sub_1'

                a =[]

                if False:
                    kprod2 = AsyncKafkaPublisher(topic,bootstrap_servers=kafka_host)
                    pipe1 = [json_message_in] > kprod2


                    ksrc1 = AsyncKafkaSource(topic,bootstrap_servers=kafka_host, value_deserializer = 'json')
                    ksrc2 = AsyncKafkaSource(topic2,bootstrap_servers=kafka_host, value_deserializer = 'json')
                    pipe1a = ksrc1 | op.map(json_to_trade)
                    pipe1b = ksrc2 | op.map(json_to_quote)

                    q_and_t = op.merge_sorted([ksrc1, ksrc2], lambda x: x.timestamp)


                    run(pipe1a, pipe1b)

                kprod = KafkaProducer(bootstrap_servers=kafka_host)
                encoded = json_message_in.encode('utf-8')
                kprod.send(topic, b'%s' % encoded)

                # read back from topic
                consumer = KafkaConsumer(topic, bootstrap_servers=kafka_host, auto_offset_reset='earliest',
                                         group_id=None)

                raw_message = next(consumer).value
                jsonMessage = raw_message.decode("utf-8")
                trade = json_to_trade(jsonMessage)

                # do assertions
                self.assertEquals(trade.duration, 18, msg=None)
                self.assertEquals(trade.delta, 1800, msg=None)
                self.assertEquals(trade.trade_date, dt.datetime(2017, 1, 16), msg=None)
                self.assertEquals(trade.notional, 1000000, msg=None)
                self.assertEquals(trade.traded_px, 1.5, msg=None)
                self.assertEquals(trade.venue, "BBGUST", msg=None)
                self.assertEquals(trade.side, TradeSide.Bid, msg=None)
                self.assertEquals(trade.timestamp, dt.datetime(2017, 1, 16, 14, 5, 0, 600000), msg=None)
        except Exception:
            raise Exception

    # Dump a json quote object into kafka and then read back and convert to Quote object
    def test_case_2(self, plotFigure=False):
        tolerance = 5 * 1e-2
        json_message_in = '{\
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
        # Load the configuration file
        configurator = Configurator('config')
        logging.basicConfig(level=configurator.get_config_given_key('log_level'))
        try:
            with ExceptionLoggingContext():
                topic = 'quote_sub_1'
                kprod = KafkaProducer(bootstrap_servers=kafka_host)
                encoded = json_message_in.encode('utf-8')
                kprod.send(topic, b'%s' % encoded)

                # read back from topic
                consumer = KafkaConsumer(topic, bootstrap_servers=kafka_host, auto_offset_reset='earliest',
                                         group_id=None)

                raw_message = next(consumer).value
                jsonMessage = raw_message.decode("utf-8")
                quote = json_to_quote(jsonMessage)

                # do assertions
                # do assertions
                self.assertEquals(quote.timestamp, dt.datetime(2017, 2, 1, 9, 36, 00), msg=None)
                self.assertEquals(quote.ask, 1.12455, msg=None)
                self.assertEquals(quote.bid, 1.12435, msg=None)
                self.assertEquals(quote.sym, '912810RB6', msg=None)

        except Exception:
            raise Exception

    # importing code from one unit test to another is a bad idea
    def get_trade(self):
        json_message = '{"bondTrade": {"negotiationId": "123456789", "orderId": "123456789::venue::date::DE10YT_OTR_111::BUY",\
            "packageId": "123456789::venue::date", "productClass": "GovtBond", "productClass1": "DE10YT",\
            "sym": "DE10YT=RR", "tenor": 30, "quantity": 1000000, "tradedPx": 1.5, "modifiedDuration": 18.0,\
            "side": "Ask", "quantityDv01": 1800.0, "issueOldness": 1,"ccy": "USD", ' \
           '"timestamp": "2017.01.16D14:05:00.600000000",\
           "tradeDate": "2017.01.16", "settlementDate": "2017.01.18", "holidayCalendar": "NYC",\
           "spotSettlementDate": "2017.01.18", "venue": "BBGUST","countryOfIssue": "US","dayCount": "ACT/ACT",' \
           '"issueDate": "2016.10.31","coupon": 1.2,"couponFrequency": "ANNUAL","maturityDate": "2047.01.18"}}'
        trade = json_to_trade(json_message=json_message)
        return trade

    # Dump a json markout message object into kafka.
    def test_case_3(self, plotFigure=False):
        trade = self.get_trade()
        # t = FixedIncomeTrade(trade_id=1, duration=20, notional=5)

        msg = MarkoutMessage2(dt=-900, trade=trade, price_markout=1, hedged_bps=0.34, hedged_cents=0.13,
                              hedged_price=1.05)

        # do assertions on the markout_message
        self.assertEqual(round(msg.bps_markout, 3), 5.556)
        self.assertEqual(msg.cents_markout, 100.0)
        self.assertEqual(msg.PV_markout, 1800)
        self.assertEqual(msg.price_markout, 1)

        json_markout = mktmsg_to_json(msg)

        # Load the configuration file
        configurator = Configurator('config')
        logging.basicConfig(level=configurator.get_config_given_key('log_level'))
        try:
            with ExceptionLoggingContext():
                topic = 'markout_pub_1'
                kprod = KafkaProducer(bootstrap_servers=kafka_host)
                encoded = json_markout.encode('utf-8')
                kprod.send(topic, b'%s' % encoded)

                # read back from topic
                consumer = KafkaConsumer(topic, bootstrap_servers=kafka_host, auto_offset_reset='earliest',
                                         group_id=None)

                raw_message = next(consumer).value
                jsonMessage = raw_message.decode("utf-8")
                print(jsonMessage)
        except Exception:
            raise Exception