DOCKER_REGISTRY = pmodernell/lorawan-conformance

NAME_SCH=downlink-configure
NAME_AGENT=pmodernell-conformance-agent
DOCKER_NAME_SCH=eu.gcr.io/engineering-test-197116/$(NAME_SCH)
DOCKER_NAME_AGENT=eu.gcr.io/engineering-test-197116/$(NAME_AGENT)
VERSION=0.1.4-cmt_rejoin_persistence
DOCKER_NAME_SCH_FULL=$(DOCKER_NAME_SCH):$(VERSION)
DOCKER_NAME_AGENT_FULL=$(DOCKER_NAME_AGENT):$(VERSION)
DOCKER_VOLUME=$(shell pwd)
DOCKER_VOLUME_REPORTS=$(shell pwd)/reports

up:
	docker-compose up --force-recreate

down:
	docker-compose down

stop:
	docker-compose stop

build:
	docker-compose build

build:
	docker-compose build

clean:
	@find . -iname "*~" | xargs rm 2>/dev/null || true
	@find . -iname "*.pyc" | xargs rm 2>/dev/null || true
	@find . -iname "build" | xargs rm -rf 2>/dev/null || true

build_scheduler: clean
	@cp -r ~/.ssh .
	install -C -m 777 downlink_scheduler_tool/devices_data.py.example downlink_scheduler_tool/devices_data.py
	docker build -f Dockerfile.scheduler -t $(DOCKER_NAME_SCH_FULL) .
	docker build -f Dockerfile.agent -t $(DOCKER_NAME_AGENT_FULL) .
	@rm -r .ssh


bootstrap_test_session:
	docker-compose up -d message-broker
	@echo "Preparing test environment..."
	@sleep 10
	docker-compose up -d command-manager notification-displayer agent-mock
	@sleep 10
	@echo "Ready. Open Notification Displayer Web (http://localhost:8081/) and launch session."

launch_test_session: bootstrap_test_session
	docker-compose up -d test-application-server

agent_mock_logs:
	docker logs $(docker-compose ps -q agent-mock) -f

open_cli:
	docker-compose run --rm cli bash

publish_scheduler: build_scheduler
	@docker push $(DOCKER_NAME_SCH_FULL)
	@docker push $(DOCKER_NAME_AGENT_FULL)

config_scheduler:
	docker-compose up -d message-broker postgres agent-scheduler config-scheduler

