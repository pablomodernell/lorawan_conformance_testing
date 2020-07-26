FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/agent"
RUN mkdir logs

# Application deps
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
COPY supervisor/agent/supervisord.conf.ini supervisord.conf.ini
# COPY conf.d/ conf.d/

COPY lorawan lorawan
COPY conformance_testing conformance_testing
COPY parameters parameters
COPY utils.py utils.py
COPY message_queueing.py message_queueing.py
COPY logger_configurator.py logger_configurator.py
COPY user_interface user_interface

# Define environment variable
ENV PYTHONPATH /agent/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
