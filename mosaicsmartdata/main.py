import sys, getopt, logging

def get_pipelines():
    pipeline1 = src | ... | ... > ...
    pipeline2 = src | ... | ... > ...
    return [pipeline1, pipeline2]

def get_pipeline_names():
    return ['pipe_1','pipe_2']


def main(argv):
    if 'ID' in argv:
        process_ID = argv['ID']
    else:
        process_ID = ''

    pipe_names = get_pipeline_names()
    pipe_UIDs = [process_ID + pname for pname in pipe_names]
    # set up persistence logic
    if 'persist' in argv and argv['persist']:

        persistence = KafkaPersistence(period = 600) # every 10 min

        try:
            pipelines = persistence.load(pipe_UIDs)
        except: #
            pipelines = get_pipelines()
            logging.exception('couldn`t reflate pipelines') #TODO include exception details


    for i,pipeline in enumerate(pipelines):
        pipeline.persistence = persistence
        pipeline.id = pipe_UIDs[i]

    run(*pipelines)





if __name__ == "__main__":
   main(sys.argv[1:])