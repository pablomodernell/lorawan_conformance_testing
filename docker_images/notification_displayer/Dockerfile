FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes git \
                                          python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/notification_displayer"
RUN mkdir logs

# Application deps
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

RUN rm -rf requirements.txt

COPY parameters parameters
COPY message_queueing.py message_queueing.py
COPY user_interface user_interface
COPY logger_configurator.py logger_configurator.py

ENV PYTHONPATH /notification_displayer/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8