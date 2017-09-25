#!/bin/bash

pwd

./broker_helpers/wait-for-it.sh -t 120 zookeeper:2181
result=$?

echo Zookeeper online result: ${result}

./broker_helpers/wait-for-it.sh -t 120 kafka:9092
result=$?

echo Kafka online result: ${result}

cd $KAFKA_HOME

echo "Creating topics"

./bin/kafka-topics.sh --zookeeper zookeeper --create --topic bond-trades-topic --partitions 1 --replication-factor 1

echo "Waiting 5s for topic to be created"

sleep 5

echo "Loading bond trades from file"

if [ ! -f "/broker_helpers/bond-trades.txt" ]; then
  echo "Error did not find file of bond trades"
  exit 1
fi

echo "Pushing bond-trades into the bond-trades-topic"

./bin/kafka-console-producer.sh --broker-list kafka:9092 --topic bond-trades-topic < /broker_helpers/bond-trades.txt
