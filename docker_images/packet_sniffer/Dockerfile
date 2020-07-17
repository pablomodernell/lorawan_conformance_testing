FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/sniffer"
RUN mkdir logs

# Application deps
ADD requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
ADD supervisor/packet_sniffer/supervisord.conf.ini supervisord.conf.ini

ADD lorawan lorawan
ADD conformance_testing conformance_testing
ADD parameters parameters
ADD utils.py utils.py
ADD message_queueing.py message_queueing.py
ADD user_interface user_interface
ADD packet_sniffer packet_sniffer
ADD packet_sniffer/sniffer packet_sniffer/sniffer

RUN python3 -m pip install packet_sniffer/sniffer

# Define environment variable
ENV PYTHONPATH /sniffer/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
