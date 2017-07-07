import importlib
import logging

importlib.reload(logging)
# logging.basicConfig(level = logging.INFO)
from unittest import TestCase
import random
import os, inspect
from aiostreams import run, ExceptionLoggingContext, AsyncKafkaPublisher, AsyncKafkaSource
from aiostreams.main import main_function
from mosaicsmartdata.common.test_utils import read_quotes_trades
from mosaicsmartdata.core.markout_basket_builder import *

from mosaicsmartdata.wrappers.markout_pipeline import pipeline_fun

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
        with ExceptionLoggingContext():
            dump1 = quotes > AsyncKafkaPublisher(quotes_topic)
            dump2 = trades > AsyncKafkaPublisher(trades_topic)
            run(dump1, dump2)

        # put together the args for the main wrapper
        class Dummy:
            pass

        args = Dummy()
        args.reload = False
        args.logfile = None
        args.loglevel = 'INFO'
        args.id = 'Unhedgded_bond_markouts_'
        args.persist_topic = None
        args.kafka_broker = None
        args.input_topics = quotes_topic + ',' + trades_topic
        args.output_topic = output_topic

        # get the nice pipeline and run it
        # TODO: next step, call the main function instead!
        # pipeline_name = pipeline_fun(True)[0]
        # pipeline = pipeline_fun(False,
        #                         input_topics = [quotes_topic, trades_topic],
        #                         output_topic = output_topic)[pipeline_name]
        main_function(args, pipeline_fun)

        with ExceptionLoggingContext():
            graph = AsyncKafkaSource(output_topic) > []
            run(graph)

        print(graph.sink)

if __name__ == '__main__':
    #    unittest.main()
    k= TestCommandLine()
    k.setUp()
    k.test_app_wrapper()
