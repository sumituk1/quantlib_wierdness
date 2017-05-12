#!/bin/bash

pwd

./broker_helpers/wait-for-it.sh -t 120 kafka:9092
result=$?

cd $KAFKA_HOME

./bin/kafka-topics.sh --zookeeper zookeeper --create --topic topic-a --partitions 1 --replication-factor 1
./bin/kafka-topics.sh --zookeeper zookeeper --create --topic topic-b --partitions 1 --replication-factor 1

sleep 10

python /scripts/start-app.py