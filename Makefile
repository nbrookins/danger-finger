
#!make

env=""
#always load build.env
include env/build.env
export $(shell sed 's/=.*//' env/build.env)
env_file_param=--env-file env/build.env
#now also parse any other files they passed in env=
ifeq ($(env),"")
	#automatic detect environ
	include env/$(environ).env
	export $(shell sed 's/=.*//' env/$(environ).env)
	env_file_param=--env-file env/$(environ).env
else
	#manually passed env param
	include $(env)
	export $(shell sed 's/=.*//' $(env))
	env_file_param=--env-file $(env)
endif

# If the first argument is "run" then fix other params to pass along
ifeq (run,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif

# This will be overrdden with harbor.smartdrivesystems.com in Jenkins CI
# if we leave blank, seems to work well for targeting locally when disconnected.  needs trailing slash however!
DOCKER_REGISTRY ?= # harbor.smartdrivesystems.com/

# This will be overrdden with an actual build number in Jenkins CI
BUILD_NUMBER ?= $(environ)

# This will be overridden with 'common' in Jenkins CI
HARBOR_PROJECT ?= sandbox

DOCKER_TAG ?= $(DOCKER_REGISTRY)$(HARBOR_PROJECT)/$(project):$(version)-$(BUILD_NUMBER)

build:
	make build_cmd
	make list

build_cmd:
	#make build_script_prep
	make build_internal

build_internal:
	docker build --rm --compress \
		--build-arg py3=$(py3) \
		--tag $(DOCKER_TAG) .
	docker build --rm --compress \
		--build-arg py3=$(py3) \
		--tag $(project):latest .

#build_script_prep::
	#pwd
	#do something special

list:
	#Checking for running instances
	docker ps -q | grep "$(project)"; echo
	#Checking built images
	docker image list | grep "$(project)"; echo

#removed run-service, as there's no difference.  can always be added in child makefile if desired.
run:
	docker run \
	  -e project=$(project) \
	  -e script=$(script) \
	  -p 8081:8081/tcp \
	  --log-opt tag="project=$(project)," \
	  -e domain=$(domain) \
	  $(env_file_param) $(DOCKER_TAG) $(RUN_ARGS)

run-shell:
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

kill-all:
	docker kill $$(docker ps -q ) ; echo

kbr:
	make kill-all
	make build
	make run

kbrs:
	make kill-all
	make build
	make run-shell

stop:
	echo $(shell docker ps | grep "$(project)" | awk '{print $$1}') | xargs docker stop ; echo

stop-all:
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
