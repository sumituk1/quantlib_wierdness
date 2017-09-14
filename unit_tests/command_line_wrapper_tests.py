import importlib
import logging

importlib.reload(logging)
# logging.basicConfig(level = logging.INFO)
from unittest import TestCase
import random
import os, inspect
from aiostreams import run, ExceptionLoggingContext, AsyncKafkaPublisher, AsyncKafkaSource
from aiostreams.main import main_function
import aiostreams.operators as op
from mosaicsmartdata.common.test_utils import read_quotes_trades
from mosaicsmartdata.core.markout_basket_builder import *
from mosaicsmartdata.common.json_convertor import json_to_domain, domain_to_json

from mosaicsmartdata.wrappers.markout_pipeline import pipeline_fun_unhedged

thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
os.chdir(thisfiledir)


class TestCommandLine(TestCase):
    def test_app_wrapper(self):

        quotes_topic = 'quotes_' + str(random.randint(1, 100000))
        trades_topic = 'trades_' + str(random.randint(1, 100000))
        output_topic = 'markouts_' + str(random.randint(1, 100000))
        # get data
        quotes, trades = read_quotes_trades(datapath="../resources/unhedged_markout_tests/",
                                            quote_file_list=["912810RB6_quotes.csv",
                                                             "DE10YT_RR_quotes.csv",
                                                             "US30YT_RR_quotes.csv"],
                                            trade_file="trades.csv")
        # dump it onto Kafka topics
        logging.getLogger().setLevel('INFO')
        logging.info('staring command line test...')

        def object_dumper(source, topic):
            return source | op.map(domain_to_json) > \
                   AsyncKafkaPublisher(topic, value_serializer= lambda x: x.encode('utf-8'))

        with ExceptionLoggingContext():
            dump1 = object_dumper(quotes, quotes_topic)
            dump2 = object_dumper(trades, trades_topic)
            run(dump1, dump2)
            logging.getLogger(__name__).info('Dumped ' + str(dump1.message_count) + ' quotes and ' + str(dump2.message_count) + ' trades')

        # put together the args for the main wrapper
        class Dummy:
            pass

        args = Dummy()
        args.reload = False
        args.logfile = None
        args.loglevel = 'INFO'
        args.id = 'Unhedgded_bond_markouts_'
        args.persist_topic = None
        args.kafka_broker = 'kafka'
        args.input_topics = quotes_topic + ',' + trades_topic
        args.output_topic = output_topic
        args.test_mode = True # that makes the function time out after 500ms, rather than waiting for looong time for inputs
        args.persist = False

        main_function(args, pipeline_fun_unhedged)

        with ExceptionLoggingContext():
            graph = AsyncKafkaSource(output_topic, value_deserializer= lambda x: x.decode('utf-8'))  > []
                    #| op.map(json_to_domain) > []
            run(graph)

        with ExceptionLoggingContext():
            pass # gently shut down

        print(len(graph.sink))
        print(graph.sink[0])

if __name__ == '__main__':
    #    unittest.main()
    k= TestCommandLine()
    k.setUp()
    k.test_app_wrapper()
