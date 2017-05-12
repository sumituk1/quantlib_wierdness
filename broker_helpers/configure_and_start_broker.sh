pwd
./wait-for-it.sh -t 120 zookeeper:2181
result=$?

echo Zookeeper online result: ${result}

cd $KAFKA_HOME

export BROKER_ID=$(hostname -i | sed 's/\([0-9]*\.\)*\([0-9]*\)/\2/')
sed -i 's/^\(broker\.id=\).*/\1'$BROKER_ID'/' config/server.properties

sed -i 's|^#\(listeners=PLAINTEXT://\)\(:9092\)|\1'`hostname -i`'\2|' config/server.properties

sed -i 's|^\(zookeeper.connect=\)\(localhost\)\(:2181\)|\1zookeeper\3|' config/server.properties

# this must run in the background otherwise it will block and the application will never get started
./bin/kafka-server-start.sh config/server.properties