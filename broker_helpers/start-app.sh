#!/bin/bash

pwd

./broker_helpers/wait-for-it.sh -t 120 kafka:9092
result=$?

# Give the Kafka Service time to create the topics
sleep 10

python /scripts/start-app.py