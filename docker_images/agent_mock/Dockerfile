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

# Application deps
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN rm -rf requirements.txt

COPY agent_tools_dist/lorawan_conformance-1.1.2-py3-none-any.whl agent_tools_dist/lorawan_conformance-1.1.2-py3-none-any.whl
RUN python3 -m pip install agent_tools_dist/lorawan_conformance-1.1.2-py3-none-any.whl

# Define environment variables
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

