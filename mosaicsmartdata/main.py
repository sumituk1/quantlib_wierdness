import sys, getopt, logging
sys.path.append('../../quant_container')
from aiostreams import run
from aiostreams.config import QCConfigProvider
import aiostreams.operators as op
from aiostreams.persist import KafkaPersister, SimplePersistencePolicy
from aiostreams.context import ExceptionLoggingContext

def get_pipelines():
    result = []
    pipeline1 = range(10) | op.map(lambda x: 2*x) > result
    pipeline1.result = result
#    pipeline2 = src | ... | ... > ...
    return [pipeline1]

def get_pipeline_names():
    return ['pipe_1']


def main(args):
    with ExceptionLoggingContext():
        if args.id is not None:
            process_ID = args.id
        else:
            process_ID = 'test_pid_'

        config = QCConfigProvider()
        if args.persist_topic is not None:
            config.persist_kafka_topic = args.persist_topic
        if args.kafka_broker is not None:
            config.kafka_broker = args.kafka_broker

        pipe_names = get_pipeline_names()
        pipe_UIDs = [process_ID + pname for pname in pipe_names]
        # set up persistence logic
        persister = KafkaPersister()  # every 10 min
        if args.reload:
            try:
                pipelines = [persister.load(p) for p in pipe_UIDs]
            except: #
                pipelines = get_pipelines()
                logging.exception('couldn`t reflate pipelines') #TODO include exception details
        else:
            pipelines = get_pipelines()


        for i,pipeline in enumerate(pipelines):
            pipeline.persister = persister
            pipeline.persistence_policy = SimplePersistencePolicy()
            pipeline.id = pipe_UIDs[i]

        run(*pipelines)
        print(pipelines[0].result)


if __name__ == "__main__":
    #  main(sys.argv[1:])

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='process ID to use for caching/retrieval')
    parser.add_argument('-r','--reload', help='Set this to reload cached graphs', action = 'store_true')
    parser.add_argument('--kafka_broker', help='Kafka IP:port')
    parser.add_argument('--persist_topic', help='Kafka topic for object persistence')

    args = parser.parse_args()
    main(args)