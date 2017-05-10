#! /bin/bash

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

function do_docker_link_source_run_bash {

	docker run -it -v `pwd`:/code/msq-domain --entrypoint=/bin/bash nexus.mosaicsmartdata.com:8083/mosaicsmartdata/quant-container:latest
}

function do_docker_link_source_run_pyb_build_without_tty {

	# design for build systems to run, locally you will need the -t flag

	docker run -i -v `pwd`:/code/msq-domain --entrypoint=/bin/bash nexus.mosaicsmartdata.com:8083/mosaicsmartdata/docker-anaconda3-ubuntu:1.0 "/code/msq-domain/install-deps-and-integration-test.sh"
}

function do_pyb_skip_tests {

	pyb -x run_unit_tests -x verify clean publish
}

function do_pyb_run_integraton_tests {

	# run from your host directly, requires docker-compose installed

	docker-compose -f docker-compose.tests.yml down
	docker-compose -f docker-compose.tests.yml up

	# TODO
	# docker-compose -f docker-compose.tests.yml up -d
	# docker-compose -f docker-compose.tests.yml wait
	# validate results in container
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
pyb_skip_tests)
   do_pyb_skip_tests
   ;;   
pyb_run_integraton_tests)
   do_pyb_run_integraton_tests
   ;;
 *)
   echo "Usage: dockerctrl {build_image|tag_image|push_image|pull_image|btp_image|link_source|run_build|ps}" >&2
   echo
   echo "link_source              - links current source directory into docker container" >&2
   echo "pyb_skip_tests           - runs pybuilder without tests" >&2
   echo "pyb_run_integraton_tests - runs pybuilder with ZK, Kafka including integration tests" >&2
   exit 3
   ;;
esac