import sys, getopt, logging
from aiostreams import run
from aiostreams.persist import KafkaPersister, SimplePersistencePolicy
import random

def get_pipelines():
    pipeline1 = src | ... | ... > ...
    pipeline2 = src | ... | ... > ...
    return [pipeline1, pipeline2]

def get_pipeline_names():
    return ['pipe_1','pipe_2']


def main(argv):
    if 'id' in argv:
        process_ID = argv['id']
    else:
        process_ID = 'test_pid_'

    pipe_names = get_pipeline_names()
    pipe_UIDs = [process_ID + pname for pname in pipe_names]
    # set up persistence logic
    if 'load_persisted' in argv:
        persister = KafkaPersister() # every 10 min

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





if __name__ == "__main__":
   main(sys.argv[1:])