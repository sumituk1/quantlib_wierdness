FROM nexus.mosaicsmartdata.com:8083/mosaicsmartdata/quant-container:latest

ADD target/dist/msq-domain-1.0.dev0/dist/msq-domain-1.0.dev0.tar.gz /

RUN pip install --upgrade pip \
    && cd msq-domain-1.0.dev0 \
    && pip install . \
    && cp -ra /msq-domain-1.0.dev0/scripts / \
    && rm -rf /msq-domain-1.0.dev0

CMD ['/bin/bash']