FROM nexus.mosaicsmartdata.com:8083/mosaicsmartdata/quant-container:latest

ADD target/dist/msq-domain-1.0.dev0/dist/msq-domain-1.0.dev0.tar.gz /

RUN cd msq-domain-1.0.dev0 \
    && python setup.py install \
    && rm -rf /msq-domain-1.0.dev0

CMD ['/bin/bash']