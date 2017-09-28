
# Debugging

To help debug there is a docker-compose-debug.yml configuration that starts 4 services:

* 1 Zookeeper
* 1 Kafka Broker
* 1 MSQ Bond application
* 1 Bond Trade Producer

When the configuration is run trades will be injected and the processing will be written to a log file.

## Bond Trade Producer

Injects trade messages in the /broker_helpers/bond-trades.txt file into bond-trades-topic when the following is executed:
```/broker_helpers/load_bond_trades.sh.
```

## MSQ Bond Application

From a base quant-container image, this configuration does a number of things when the following is executed:
```command: "/bin/bash /code/msx.sh start_unhedged"
```

* Binds the source code on your host into the container
* Compiles and builds a new local version of msq-domain into /target
* Executes the unhedged script in the target folder with logging configured to write to:
```target/application.log
```

## Start Debug

./msx.sh start_debug

## Stop Debug

./msx.sh stop_debug

## Log output_topic

Written to ```target/application.log

```
