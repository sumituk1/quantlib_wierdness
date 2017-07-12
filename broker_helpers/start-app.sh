#!/bin/bash

pwd

echo "Waiting upto 120 seconds for Kafka:9092 to be online"

./broker_helpers/wait-for-it.sh -t 120 kafka:9092
result=$?

echo "Sleeping for 15 seconds to give the Kafka Service time to create the topics"

sleep 15

echo "Executing start-app.py script"

python /scripts/start-app.py --kafka_broker kafka --loglevel DEBUG --input_topics topic-a,topic-b --output_topic output-topic
