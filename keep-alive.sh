#!/bin/bash

# Starts a http web server to keep the contain online so that you can attach to 
# it and executes things for debugging

cd /code
python -m http.server 8000