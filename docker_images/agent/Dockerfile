FROM python:3.6.8-alpine3.7

# Install requirements
RUN apk add --update-cache --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ \
    python3 git musl-dev gcc postgresql-dev && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

WORKDIR "/agent"
RUN mkdir logs

# Application deps
RUN python3 -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

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
