#!/usr/bin/env python

from aiostreams import entrypoint, get_pipelines

entrypoint(get_pipelines)

# Template for the pipeline definition function to be used instead of get_pipelines:
# def pipeline_fun(names_only=False):
#     if names_only:
#         # return a list with the names of the graphs this function makes
#     else:
#         # return a dict where the keys are graph names
#         # and the values are the graphs
#         # the keys here must be the same as the names in the list above
