#!/usr/bin/env python

# PLEASE DON'T DELETE THE BELOW 4 LINES, I COMMENT THEM IN FOR LOCAL TESTING
import os, sys, inspect
my_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(my_location+ '/../src')
sys.path.append(my_location + '/../../quant_container/src')

from aiostreams import entrypoint, get_pipelines
from mosaicsmartdata.wrappers.markout_pipeline import pipeline_fun
# Template for the pipeline definition function to be used instead of get_pipelines:
# def pipeline_fun(names_only=False, cmd_args = None):
#     if names_only:
#         # return a list with the names of the graphs this function makes
#     else:
#         # return a dict where the keys are graph names
#         # and the values are the graphs
#         # the keys here must be the same as the names in the list above
entrypoint(pipeline_fun)


