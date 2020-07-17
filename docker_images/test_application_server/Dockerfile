FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes git \
                                          python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/test_application_server"
RUN mkdir logs

# Application deps
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
COPY supervisor/test_application_server/supervisord.conf.ini supervisord.conf.ini

RUN rm -rf requirements.txt

COPY lorawan lorawan
COPY conformance_testing conformance_testing
COPY parameters parameters
COPY utils.py utils.py
COPY message_queueing.py message_queueing.py
COPY user_interface user_interface
COPY tas_application_server_main.py tas_application_server_main.py
COPY logger_configurator.py logger_configurator.py

ENV PYTHONPATH /test_application_server/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8