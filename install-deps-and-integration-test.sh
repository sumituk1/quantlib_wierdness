#!/bin/bash

#
# This script is invoked by 'docker-run-pyb-build.sh' during the build on Bamboo. The script
# installs pybuilder and then runs the build and tests.  This is needed because this container
# has the statslib and other dependencies required in order to run the tests
#

# We need some dependencies as that is not part of the base image

apt-get update -y && apt-get install vim -y
pip install --upgrade pip && pip install pybuilder --ignore-installed

# Run the build and tests with debug flag on to get some help

cd /code/msq-domain
echo Installing dependencies
pyb install_dependencies
pyb --debug

#cd ..
#jupyter notebook --no-browser --ip=0.0.0.0 --port=8888
