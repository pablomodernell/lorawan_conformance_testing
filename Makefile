DOCKER_REGISTRY=pmodernell/lorawan_conformance

# Global version for the testing platform:
VERSION=0.0.2-demo
SUFFIX=

NAME_AGENT=agent
# Specifies particular version for this service:
VERSION_AGENT=$(VERSION)$(SUFFIX)
DOCKER_NAME_AGENT=$(DOCKER_REGISTRY)-$(NAME_AGENT)
DOCKER_NAME_AGENT_FULL=$(DOCKER_NAME_AGENT):$(VERSION_AGENT)

NAME_TAS=test_application_server
# Specifies particular version for this service:
VERSION_TAS=$(VERSION)$(SUFFIX)
DOCKER_NAME_TAS=$(DOCKER_REGISTRY)-$(NAME_TAS)
DOCKER_NAME_TAS_FULL=$(DOCKER_NAME_TAS):$(VERSION_TAS)

NAME_CM=command_manager
# Specifies particular version for this service:
VERSION_CM=$(VERSION)$(SUFFIX)
DOCKER_NAME_CM=$(DOCKER_REGISTRY)-$(NAME_CM)
DOCKER_NAME_CM_FULL=$(DOCKER_NAME_CM):$(VERSION_CM)

NAME_ND=notification_displayer
# Specifies particular version for this service:
VERSION_ND=$(VERSION)$(SUFFIX)
DOCKER_NAME_ND=$(DOCKER_REGISTRY)-$(NAME_ND)
DOCKER_NAME_ND_FULL=$(DOCKER_NAME_ND):$(VERSION_ND)

NAME_AM=agent_mock
# Specifies particular version for this service:
VERSION_AM=$(VERSION)$(SUFFIX)
DOCKER_NAME_AM=$(DOCKER_REGISTRY)-$(NAME_AM)
DOCKER_NAME_AM_FULL=$(DOCKER_NAME_AM):$(VERSION_AM)

NAME_T_CS=tools_config_scheduler
# Specifies particular version for this service:
VERSION_T_CS=$(VERSION)$(SUFFIX)
DOCKER_NAME_T_CS=$(DOCKER_REGISTRY)-$(NAME_T_CS)
DOCKER_NAME_T_CS_FULL=$(DOCKER_NAME_T_CS):$(VERSION_T_CS)

NAME_T_AS=tools_agent_scheduler
# Specifies particular version for this service:
VERSION_T_AS=$(VERSION)$(SUFFIX)
DOCKER_NAME_T_AS=$(DOCKER_REGISTRY)-$(NAME_T_AS)
DOCKER_NAME_T_AS_FULL=$(DOCKER_NAME_T_AS):$(VERSION_T_AS)


# Build images:
build_conformance: clean
	@cp ~/.netrc .
	docker build -f docker_images/agent/Dockerfile -t $(DOCKER_NAME_AGENT_FULL) .
	docker build -f docker_images/test_application_server/Dockerfile -t $(DOCKER_NAME_TAS_FULL) .
	docker build -f docker_images/command_manager/Dockerfile -t $(DOCKER_NAME_CM_FULL) .
	docker build -f docker_images/notification_displayer/Dockerfile -t $(DOCKER_NAME_ND_FULL) .
	docker build -f docker_images/agent_mock/Dockerfile -t $(DOCKER_NAME_AM_FULL) .
	@rm .netrc

build_tools: clean
	@cp ~/.netrc .
	docker build -f docker_images/aux_tools/configuration_scheduler/Dockerfile -t $(DOCKER_NAME_T_CS_FULL) .
	docker build -f docker_images/aux_tools/agent_scheduler/Dockerfile -t $(DOCKER_NAME_T_AS_FULL) .
	@rm .netrc

build_agent: clean
	@cp ~/.netrc .
	docker build -f docker_images/agent/Dockerfile -t $(DOCKER_NAME_AGENT_FULL) .
	@rm .netrc

build_tas: clean
	@cp ~/.netrc .
	docker build -f docker_images/test_application_server/Dockerfile -t $(DOCKER_NAME_TAS_FULL) .
	@rm .netrc

build_cm: clean
	@cp ~/.netrc .
	docker build -f docker_images/command_manager/Dockerfile -t $(DOCKER_NAME_CM_FULL) .
	@rm .netrc

build_nd: clean
	@cp ~/.netrc .
	docker build -f docker_images/notification_displayer/Dockerfile -t $(DOCKER_NAME_ND_FULL) .
	@rm .netrc

build_agent_mock: clean
	@cp ~/.netrc .
	docker build -f docker_images/agent_mock/Dockerfile -t $(DOCKER_NAME_AM_FULL) .
	@rm .netrc

# Build auxiliary tools:
build_t_cs: clean
	@cp ~/.netrc .
	docker build -f docker_images/aux_tools/configuration_scheduler/Dockerfile -t $(DOCKER_NAME_T_CS_FULL) .
	@rm .netrc

build_t_as: clean
	@cp ~/.netrc .
	docker build -f docker_images/aux_tools/agent_scheduler/Dockerfile -t $(DOCKER_NAME_T_AS_FULL) .
	@rm .netrc

# -------------------------------------------------------------------------------------------------

clean:
	@find . -iname "*~" | xargs rm 2>/dev/null || true
	@find . -iname "*.pyc" | xargs rm 2>/dev/null || true
	@find . -iname "build" | xargs rm -rf 2>/dev/null || true

down:
	docker-compose -f docker-compose.yml down

stop:
	docker-compose -f docker-compose.yml stop

bootstrap_session_interface:
	docker-compose -f docker-compose.yml up -d --no-recreate message-broker postgres
	@echo "Preparing test environment..."
	@sleep 10
	docker-compose -f docker-compose.yml up -d --force-recreate --no-deps command-manager notification-displayer
	@sleep 2
	@echo "Ready. Open Notification Displayer Web (http://localhost:8081/) and launch session."

launch_test_session:
	docker-compose -f docker-compose.yml up -d test-application-server

start_agent:
	docker-compose -f docker-compose.yml up -d --force-recreate --no-deps agent

start_inspector:
	docker-compose -f docker-compose.yml up -d --force-recreate --no-deps agent-mock

agent_mock_logs:
	docker logs $(docker-compose ps -q agent-mock) -f

open_cli:
	docker-compose run --rm cli sh

publish_conformance: build_conformance
	@docker push $(DOCKER_NAME_AGENT_FULL)
	@docker push $(DOCKER_NAME_TAS_FULL)
	@docker push $(DOCKER_NAME_CM_FULL)
	@docker push $(DOCKER_NAME_ND_FULL)
	@docker push $(DOCKER_NAME_AM_FULL)

publish_tools: build_tools
	@docker push $(DOCKER_NAME_T_CS_FULL)
	@docker push $(DOCKER_NAME_T_AS_FULL)

config_scheduler_tools:
	docker-compose -f docker-compose.yml up -d  message-broker postgres tools-agent-scheduler tools-config-scheduler

