
#!make
environ=dev
env=""
#now also parse any other files they passed in env=
ifeq ($(env),"")
	# automatic detect environ
	include docker/$(environ).env
	export $(shell sed 's/=.*//' docker/$(environ).env)
	env_file_param=--env-file docker/$(environ).env
else
	# manually passed env param
	include $(env)
	export $(shell sed 's/=.*//' $(env))
	env_file_param=--env-file $(env)
endif

DOCKER_REGISTRY ?= # harbor.smartdrivesystems.com/
# This will be overrdden with an actual build number in Jenkins CI
BUILD_NUMBER ?= $(environ)

# If the first argument is "run" then fix other params to pass along
ifeq (run,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif

DOCKER_TAG ?= $(DOCKER_REGISTRY)$(project):$(version)-$(BUILD_NUMBER)

build:
	make build_internal
	make list

build_internal:
	docker build --rm --compress  -f docker/Dockerfile --tag $(DOCKER_TAG) . #\
	
list:
	#Checking for running instances
	docker ps -q | grep "$(project)"; echo
	#Checking built images
	docker image list | grep "$(project)"; echo

run:
	echo $(DOCKER_TAG) $(RUN_ARGS) && \
	docker run \
	  -e project=$(project) \
	  -e script=$(script) \
	  -p $(ports) \
	  --log-opt tag="project=$(project)," \
	  -e domain=$(domain) \
	  $(env_file_param) $(DOCKER_TAG) $(RUN_ARGS)

shell:
	docker run \
	  -it --entrypoint /bin/bash \
	  -e project=$(project) \
	  -e script=$(script) \
	  --log-opt tag="project=$(project)," \
	  -e domain=$(domain) \
	  $(env_file_param) $(DOCKER_TAG) $(RUN_ARGS)

attach:
	echo $(project)
	cid=$(shell docker ps | grep "$(project)" | awk '{print $$1}')
	docker exec -it $(shell docker ps | grep "$(project)" | awk '{print $$1}') /bin/bash

kill:
	killall Python
	docker kill $(shell docker ps | grep "$(project)" | awk '{print $$1}')  ; echo

killall:
	docker kill $$(docker ps -q ) ; echo

kbr:
	make killall
	make build
	make run

# Run web e2e tests against a freshly started local server (current code). No Docker, no reuse.
test-web:
	@./scripts/test_web.sh

# Build, run container in background, then run e2e test against that container only (for CI).
kbr-test:
	make killall
	make build
	@echo "Starting container in background..."
	$(MAKE) run &
	@echo "Waiting for server on port 8081..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12; do \
	  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8081/ 2>/dev/null | grep -q 200; then \
	    echo "Server up."; \
	    break; \
	  fi; \
	  sleep 2; \
	done
	USE_EXISTING_SERVER=1 TEST_PORT=8081 ./scripts/test_web.sh

# Inspect live UI in headless browser; writes ui-inspect.txt. App must be running (e.g. make kbr).
# Tighter feedback loop: after UI changes run this and check ui-inspect.txt; exit 1 = UI error.
# Requires: pip install -r requirements-dev.txt && python -m playwright install chromium
inspect-ui:
	@BASE_URL=http://127.0.0.1:8081 UI_INSPECT_OUTPUT=ui-inspect.txt $(or $(PYTHON),python3) scripts/inspect_ui.py

# Single verify run: start server (builds SCAD + PNGs at startup) + viewer screenshot (viewer-screenshot.png).
# Server creates output/ SCAD+PNGs as part of normal workflow. Use Docker (make build first) to avoid macOS OpenSCAD issues.
# Requires: make build (for Docker), pip install -r requirements-dev.txt, python -m playwright install chromium
verify-web-ui:
	@export DOCKER_TAG="$(DOCKER_TAG)" && ./scripts/verify_web_ui.sh

kbrs:
	make killall
	make build
	make shell

stop:
	echo $(shell docker ps | grep "$(project)" | awk '{print $$1}') | xargs docker stop ; echo

stopall:
	echo $$(docker ps -q) | xargs docker stop ; echo

# Run this to start the service via docker compose   -q | grep "$(project)" | awk '{print $$1}'
# After the service starts, try a 'nc -v 127.0.0.1 8000' to see the port is open
run-dc:
	docker-compose up

# Exec into bash in the service after it is running
exec-dc:
	docker-compose exec svc bash

# Run this from another terminal to stop the service via docker compose
stop-dc:
	-docker-compose down

push:
	docker push $(DOCKER_TAG)

clean:
	docker ps -a -q | xargs docker rm ; echo
	docker images -a | grep "^<none>" | awk '{print $$3}' | xargs docker rmi ; echo
	docker image list | grep "$(project)" | awk '{print $$3}' | xargs docker rmi ; echo

cleanf:
	docker ps -a -q | xargs docker rm -f ; echo
	docker images -a | awk '{print $$3}' | xargs docker rmi -f ; echo
	docker image list | grep "$(project)" | awk '{print $$3}' | xargs docker rmi -f ; echo
