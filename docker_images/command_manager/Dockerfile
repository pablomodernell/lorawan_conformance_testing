FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes git \
                                          python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/command_manager"
RUN mkdir logs

# Application deps
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

RUN rm -rf requirements.txt

COPY parameters parameters
COPY message_queueing.py message_queueing.py
COPY logger_configurator.py logger_configurator.py
COPY user_interface/command_manager .

ENV PYTHONPATH /command_manager/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8