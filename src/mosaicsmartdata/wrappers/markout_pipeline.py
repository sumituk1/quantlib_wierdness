from aiostreams import AsyncKafkaPublisher, AsyncKafkaSource, run, ExceptionLoggingContext
import aiostreams.operators as op
from mosaicsmartdata.core.markout import GovtBondMarkoutCalculator
from mosaicsmartdata.core.pca_risk import PCARisk
from mosaicsmartdata.core.markout_basket_builder import AllMarkoutFilter, PackageBuilder, aggregate_multi_leg_markouts

def pipeline_fun(names_only=False,
                 input_topics=['trades','quotes'],
                 output_topic='markouts',
                 cmd_args=None):

    if names_only:
        return ['markout_pipe']
        # return a list with the names of the graphs this function makes
    else:
        # return a dict where the keys are graph names
        # and the values are the graphs
        # the keys here must be the same as the names in the list above

        # try getting input and output topic names from command line args
        if cmd_args:
            if cmd_args.input_topics:
                input_topics = cmd_args.input_topics.split(',')
                print(input_topics)
            if cmd_args.output_topic:
                output_topic = cmd_args.output_topic

        my_name = pipeline_fun(True)[0]
        def source_wrapper(topic):
            return AsyncKafkaSource(topic, timeout_ms=1000*60*60*24*30) | op.map(lambda x: x.value)
        sources = [source_wrapper(topic) for topic in input_topics]
        run() # initialize source consumers
        stream = op.merge_sorted(sources, lambda x: x.timestamp) | op.map(PCARisk())| op.flatten()
        graph_1 = stream | op.flat_map_by_group(lambda x: x.sym, GovtBondMarkoutCalculator())

        graph_2 = graph_1 | op.flat_map_by_group(lambda x: (x.trade_id, x.dt), PackageBuilder()) \
                 | op.map(aggregate_multi_leg_markouts) | \
                  op.map_by_group(lambda x: x.package_id, AllMarkoutFilter())

        graph_3 = graph_2 > AsyncKafkaPublisher(output_topic)

        return {my_name: graph_3}