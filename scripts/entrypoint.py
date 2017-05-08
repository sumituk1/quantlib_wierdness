import argparse
import inspect, os, sys
my_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.addpath(my_location + '\\..')
from aiostreams.main import main_function


parser = argparse.ArgumentParser()
parser.add_argument('--id', help='process ID to use for caching/retrieval')
parser.add_argument('-r', '--reload', help='Set this to reload cached graphs', action='store_true')
parser.add_argument('--kafka_broker', help='Kafka IP:port')
parser.add_argument('--persist_topic', help='Kafka topic for object persistence')

args = parser.parse_args()
main_function(args)