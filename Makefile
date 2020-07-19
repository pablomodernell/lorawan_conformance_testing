DOCKER_REGISTRY = pmodernell/lorawan-conformance

up:
	docker-compose up --force-recreate

down:
	docker-compose down

stop:
	docker-compose stop

build:
	docker-compose build

bootstrap_test_session:
	docker-compose up -d message-broker
	@echo "Preparing test environment..."
	@sleep 10
	docker-compose up -d command-manager notification-displayer agent-mock
	@sleep 10
	@echo "Ready. Open Notification Displayer Web (http://localhost:8081/) and launch session."

launch_test_session: bootstrap_test_session
	docker-compose up -d test-application-server

start_agent: launch_test_session
	docker-compose up -d agent

agent_mock_logs:
	docker logs $(docker-compose ps -q agent-mock) -f

open_cli:
	docker-compose run --rm cli bash






