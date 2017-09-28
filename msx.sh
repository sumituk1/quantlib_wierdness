#! /bin/bash

#
#
#

function do_bitbucket_pyb {

	echo "Running do_bitbucket_pyb"

	pyb install_dependencies
	pyb clean publish --debug
	status=$?

	if [ ${status} -ne 0 ]; then
    echo "Failure during build...exiting"
		exit 1
	fi

	echo "Completed do_bitbucket_pyb: status $status"
}

function do_bitbucket_docker_build_push {

	echo "Working dir should be msq-domain"

	if [ ! -f Dockerfile ]; then
	    echo "Dockerfile not found, this needs to be run from the root of the project"
	    return 255
	fi

	echo "Building and Pushing nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain:latest"

	docker build -t nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain:latest .
	docker push nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain:latest
	status=$?

	if [ ${status} -ne 0 ]; then
		echo "Failure during build...exiting"
		exit 1
	fi

	echo "Completed do_bitbucket_docker_build_push status $status"
}

function do_build {

	echo "Working dir should be msq-domain"

	if [ ! -f Dockerfile ]; then
	    echo "Dockerfile not found, this needs to be run from the root of the project"
	    return 255
	fi

	echo "Building nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain image"

	docker build -t nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain .

	echo "Completed build task"
}

function do_tag {

	echo "Getting nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain Image ID"

	image_id=$(docker images -q nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain | head -1)

	echo "Tagging nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain using $image_id"

	docker tag $image_id nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain:latest

	echo "Completed tag task"
}

function do_push {

	echo "Pushing nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain"

	docker push nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain:latest

	echo "Completed push task"
}

function do_pull {

	echo "Pulling nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain"

	docker pull nexus.mosaicsmartdata.com:8083/mosaicsmartdata/msq-domain

	echo "Completed pull task"
}

function do_build_tag_push {
	do_build
	do_tag
	do_push
}

function do_build_dev_image {

	# use this target if you need to build a new dev quant-container image quickly
	# without tests for development against the msq-domain or another application
	# that sits on top of this framework

	do_pyb_skip_tests
	do_build
}

function do_docker_link_source_run_bash {

	docker run -it -v `pwd`:/code/msq-domain --entrypoint=/bin/bash nexus.mosaicsmartdata.com:8083/mosaicsmartdata/quant-container:latest
}

function do_docker_link_source_run_pyb_build_without_tty {

	# design for build systems to run, locally you will need the -t flag

	docker run -i -v `pwd`:/code/msq-domain --entrypoint=/bin/bash nexus.mosaicsmartdata.com:8083/mosaicsmartdata/quant-container:latest "/code/msq-domain/msx.sh integration_test"
}

function do_pyb_skip_tests {

    pyb install_dependencies
	pyb -x run_unit_tests -x verify clean publish
}

function do_pyb_run_integration_tests {

	# run from your host directly, requires docker-compose installed

	docker-compose down
	docker-compose up

	# TODO
	# docker-compose up -d
	# docker-compose wait
	# validate results in container
}

function install_devtools {

	# We need some dependencies as that is not part of the base image

	apt-get update -y && apt-get install vim -y
	pip install --upgrade pip && pip install pybuilder --ignore-installed
}

function do_pyb_build_all_from_source {

	# Designed to be run from wthin the container

	# This function is pretty custom and depends where in your path
	# you linked your host directory because of line
	# cd ../../../../msq-domain

	install_devtools

	# Run the build and tests with debug flag on to get some help

	cd /code/quant-container
	echo Installing dependencies
	pyb install_dependencies
	pyb --debug

	# now install that package

	cd target/dist/quant_container-1.0.dev0
	python setup.py install

	# and now try building msq-domain
	cd /code/msq-domain
	pyb install_dependencies
	pyb --debug
}

function do_load_bond_trades {

	# Designed to be run from wthin the container

	install_devtools

	# Run the build and tests with debug flag on to get some help

	cd /code
	echo Loading bond trades from file into Kafka console consumer

	kafka-console-producer.sh --broker-list localhost:9092 --topic topic-a < my_file.txt

}

function do_integration_test {

	# Designed to be run from wthin the container

	install_devtools

	# Run the build and tests with debug flag on to get some help

	cd /code
	echo Installing dependencies
	pyb install_dependencies
	pyb --debug

}

function start_jupyter {

	# Designed to be run from wthin the container

	install_devtools

	# Start jupyter
  cd /code
	echo Installing dependencies
	pyb install_dependencies
  pyb -x run_unit_tests -x verify clean publish

#    RUN pip install --upgrade pip \
#    && cd msq-domain-1.0.dev0 \
#    && pip install . \
#    && cp -ra /msq-domain-1.0.dev0/scripts / \
#    && rm -rf /msq-domain-1.0.dev0

    cd /code/target/dist/msq-domain-1.0.dev0
    pip install .

    # The below is an ugly hack until we can figure out how to make project.include_directory work in build.py
    cp mosaicsmartdata/configuration/*.csv  /opt/conda/lib/python3.5/site-packages/mosaicsmartdata/configuration/

    #cd scripts
    python ./start-app-hedged.py --kafka_broker kafka --loglevel DEBUG --input_topics topic-a,topic-b --output_topic output-topic

	  jupyter notebook --no-browser --ip=0.0.0.0 --port=8888


}

function do_attach {

	docker exec -it $1 /bin/bash
}

function do_attach_msq_domain {

	do_attach msqdomain_myapp_1
}

function do_wait_for_kafka {
  echo "Waiting upto 120 seconds for Kafka:9092 to be online"
  ./broker_helpers/wait-for-it.sh -t 120 kafka:9092
  result=$?
}

function do_keep_alive {
  echo "Executing keep_alive"
  tail -f /dev/null
}

# function do_start_hedged {
#   echo "Executing start-app-hedged.py"
#   do_wait_for_kafka
#   python /scripts/start-app-hedged.py --kafka_broker kafka --loglevel DEBUG --input_topics bond-trades-topic,bond-quotes-topic --output_topic output-topic
# }
#
# function do_start_unhedged {
#   echo "Executing start-app-hist-unhedged.py"
#   do_wait_for_kafka
#   cd /
#   ls -l scripts
#   jupyter notebook --no-browser --ip=0.0.0.0 --port=8999 &
#   python /scripts/start-app-hist-unhedged.py --kafka_broker kafka --loglevel DEBUG --input_topics bond-trades-topic --output_topic output-topic --logfile /code/logs/application.log
# }

function do_start_unhedged {
	install_devtools
  cd /code
	ls -1
	echo Installing dependencies
	pyb install_dependencies
  pyb -x run_unit_tests -x verify clean publish
  cd /code/target/dist/msq-domain-1.0.dev0
  pip install .
  cp mosaicsmartdata/configuration/*.csv  /opt/conda/lib/python3.5/site-packages/mosaicsmartdata/configuration/
  python ./scripts/start-app-hist-unhedged.py --kafka_broker kafka --loglevel DEBUG --input_topics bond-trades-topic --output_topic output-topic --logfile /code/target/application.log
	jupyter notebook --no-browser --ip=0.0.0.0 --port=8888
}

function do_start_debug {

	docker-compose -f docker-compose-debug.yml down
	docker-compose -f docker-compose-debug.yml up -d
}

function do_stop_debug {

	docker-compose -f docker-compose-debug.yml down
}

case "$1" in
 build_image)
   do_build
   ;;
 tag_image)
   do_tag
   ;;
 push_image)
   do_push
   ;;
 pull_image)
   do_pull
   ;;
 btp_image)
   do_build_tag_push
   ;;
link_source)
   do_docker_link_source_run_bash
   ;;
run_build)
   do_docker_link_source_run_pyb_build_without_tty
   ;;
ps)
   docker ps
   ;;
build_dev_image)
   do_build_dev_image
   ;;
pyb_skip_tests)
   do_pyb_skip_tests
   ;;
pyb_run_integration_tests)
   do_pyb_run_integration_tests
   ;;
pyb_build_all_from_source)
  do_pyb_build_all_from_source
  ;;
integration_test)
   do_integration_test
   ;;
jupyter)
   start_jupyter
   ;;
attach)
   do_attach_msq_domain
   ;;
attach_msq_domain)
   do_attach_msq_domain
   ;;
bitbucket_pyb)
   do_bitbucket_pyb
	 ;;
bitbucket_docker_build_push)
   do_bitbucket_docker_build_push
	 ;;
start_unhedged)
  do_start_unhedged
	;;
start_debug)
  do_start_debug
	;;
stop_debug)
  do_stop_debug
	;;
*)
   echo "Usage: dockerctrl {build_image|tag_image|push_image|pull_image|btp_image|link_source|run_build|ps}" >&2
   echo
   echo "link_source              - links current source directory into docker container" >&2
   echo "pyb_skip_tests           - runs pybuilder without tests" >&2
   echo "pyb_run_integration_tests - runs pybuilder with ZK, Kafka including integration tests" >&2
   exit 3
   ;;
esac
