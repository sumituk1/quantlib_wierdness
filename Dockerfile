FROM nexus.mosaicsmartdata.com:8083/mosaicsmartdata/quant-container:latest

WORKDIR code

ADD target/dist/msq-domain-1.0.dev0/dist/msq-domain-1.0.dev0.tar.gz /code/
ADD /broker_helpers/start-app.sh /code/
ADD /broker_helpers/wait-for-it.sh /code/broker_helpers/
#ADD /broker_helpers/requires-topic.dat /code/
ADD /src/mosaicsmartdata/configuration/*.csv  /opt/conda/lib/python3.5/site-packages/mosaicsmartdata/configuration/

RUN apt-get update -y && apt-get install vim -y \
    && pip install --upgrade pip \
    && pip install pybuilder --ignore-installed \
    && cd /code/msq-domain-1.0.dev0 \
    && pip install . \
    && cp -ra /code/msq-domain-1.0.dev0/scripts / \
    && rm -rf /code/msq-domain-1.0.dev0

ENTRYPOINT ["/bin/bash"]
#ENTRYPOINT ["bash", "./start-app.sh", "0"]
