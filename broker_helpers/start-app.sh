#!/bin/bash

pwd

./broker_helpers/wait-for-it.sh -t 120 kafka:9092
result=$?

python /scripts/start-app.py