FROM ubuntu
# System wide deps
RUN apt-get update; apt-get install --yes git \
                                          python3 \
                                          python3-dev \
                                          python3-pip \
                                          supervisor \
                                          iputils-ping \
                                          make

WORKDIR "/agent_mock"
RUN mkdir logs

# Adding credentials for git cloning
ENV HOME /root
COPY .netrc $HOME/

# Application deps
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN rm -rf requirements.txt

# Removing credentials
RUN rm -rf $HOME/.netrc

# COPY agent_tools_dist/lorawan_conformance-1.1.2-py3-none-any.whl agent_tools_dist/lorawan_conformance-1.1.2-py3-none-any.whl
# RUN python3 -m pip install agent_tools_dist/lorawan_conformance-1.1.2-py3-none-any.whl

COPY lorawan lorawan
COPY conformance_testing conformance_testing
COPY parameters parameters
COPY utils.py utils.py
COPY message_queueing.py message_queueing.py
COPY logger_configurator.py logger_configurator.py

# Define environment variables
ENV PYTHONPATH /agent_mock/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

