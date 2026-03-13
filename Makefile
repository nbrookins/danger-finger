
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
# Overridden by Jenkins CI; locally defaults to environ + git short SHA for traceability
BUILD_NUMBER ?= $(environ)-$(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)

# If the first argument is "run" then fix other params to pass along
ifeq (run,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif

DOCKER_TAG ?= $(DOCKER_REGISTRY)$(project):$(version)-$(BUILD_NUMBER)

echo-tag:
	@echo $(DOCKER_TAG)

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

# Inspect live UI in headless browser; writes output/ui-inspect.txt. App must be running (e.g. make kbr).
# Tighter feedback loop: after UI changes run this and check output/ui-inspect.txt; exit 1 = UI error.
# Requires: pip install -r requirements-dev.txt && python -m playwright install chromium
inspect-ui:
	@BASE_URL=http://127.0.0.1:8081 UI_INSPECT_OUTPUT=output/ui-inspect.txt $(or $(PYTHON),python3) scripts/inspect_ui.py

# Single verify run: start server (builds SCAD + PNGs at startup) + viewer screenshot (output/viewer-screenshot.png).
# Server creates output/ SCAD+PNGs as part of normal workflow. Use Docker (make build first) to avoid macOS OpenSCAD issues.
# Requires: make build (for Docker), pip install -r requirements-dev.txt, python -m playwright install chromium
verify-web-ui:
	@export DOCKER_TAG="$(DOCKER_TAG)" && ./scripts/verify_web_ui.sh

# --- AWS deployment targets ---

AWS_REGION ?= us-east-1
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REPO = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(project)

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

push-ecr: ecr-login
	docker tag $(DOCKER_TAG) $(ECR_REPO):$(version)-$(BUILD_NUMBER)
	docker tag $(DOCKER_TAG) $(ECR_REPO):latest
	docker push $(ECR_REPO):$(version)-$(BUILD_NUMBER)
	docker push $(ECR_REPO):latest

deploy-lambda:
	cd infra && terraform apply -auto-approve -target=aws_lambda_function.s3_read -target=aws_lambda_layer_version.brotli -var-file=environments/$(environ).tfvars

JWT_SECRET     ?= $(jwt_secret)
WP_AUTH_URL    ?= $(wp_auth_url)
APP_BASE_URL   ?= $(app_base_url)
STATIC_SITE_URL ?= $(static_site_url)

deploy-ec2:
	@echo "Updating EC2 container via SSM..."
	@INSTANCE_ID=$$(cd infra && terraform output -raw ec2_instance_id) && \
	aws ssm send-command --instance-ids $$INSTANCE_ID --document-name "AWS-RunShellScript" \
	  --parameters "commands=[\"docker pull $(ECR_REPO):latest && docker stop $(project) || true && docker rm $(project) || true && docker run -d --restart=unless-stopped --name $(project) -p 8081:8081 -e S3_BUCKET=$(project) -e AWS_DEFAULT_REGION=$(AWS_REGION) -e jwt_secret=$(JWT_SECRET) -e wp_auth_url=$(WP_AUTH_URL) -e app_base_url=$(APP_BASE_URL) -e static_site_url=$(STATIC_SITE_URL) $(ECR_REPO):latest\"]" \
	  --region $(AWS_REGION)

deploy-infra:
	cd infra && terraform plan -var-file=environments/$(environ).tfvars -out=tfplan && terraform apply tfplan

deploy: build push-ecr deploy-infra
	@echo "Full deployment complete."

test-deploy:
	@./scripts/verify_aws_deploy.sh

verify-aws: test-deploy

audit-aws:
	@$(or $(PYTHON),python3) scripts/aws_audit.py

benchmark-ec2:
	@$(or $(PYTHON),python3) scripts/benchmark_ec2.py

STATIC_BUCKET ?= danger-finger-static
READ_URL ?= $(shell cd infra && terraform output -raw api_gateway_url 2>/dev/null)
# Render URL uses CloudFront (same-origin) so HTTPS pages don't hit mixed-content.
RENDER_URL ?= $(shell cd infra && terraform output -raw static_site_https_url 2>/dev/null)/
# Use CloudFront HTTPS URL so the site can be embedded in the HTTPS WordPress page.
STATIC_SITE_URL ?= $(shell cd infra && terraform output -raw static_site_https_url 2>/dev/null)

generate-static:
	@$(or $(PYTHON),python3) scripts/generate_static.py

deploy-static: generate-static
	@echo "Deploying static site to s3://$(STATIC_BUCKET)..."
	@cp web/index.html web/static/index.html
	@sed -i.bak 's|</head>|<script>window.__READ_URL__="$(READ_URL)";window.__RENDER_URL__="$(RENDER_URL)";</script></head>|' web/static/index.html && rm -f web/static/index.html.bak
	aws s3 sync web/ s3://$(STATIC_BUCKET)/ \
		--exclude "*.py" --exclude "__pycache__/*" --exclude "static/*" \
		--delete --cache-control "max-age=300"
	aws s3 sync web/static/ s3://$(STATIC_BUCKET)/ --cache-control "max-age=60"
	aws s3 cp web/static/api/parts.json s3://$(STATIC_BUCKET)/api/parts \
		--content-type "application/json" --cache-control "max-age=60"
	aws s3 cp web/static/params/all.json s3://$(STATIC_BUCKET)/params/all \
		--content-type "application/json" --cache-control "max-age=60"
	@echo "Static site deployed: http://$(STATIC_BUCKET).s3-website-us-east-1.amazonaws.com"

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

# --- Regression and validation targets ---

# Build reference STLs at default params for regression baseline
reference-stls:
	@$(or $(PYTHON),python3) scripts/reference_stls.py

# Check current STL output against reference baseline
regression-check:
	@$(or $(PYTHON),python3) scripts/regression_check.py

# Validate a derived formula by sweeping params
# Usage: make validate-formula PART=tip PARAMS=tip_circumference STEPS=5
PART ?= tip
PARAMS ?= tip_circumference
STEPS ?= 5
validate-formula:
	@$(or $(PYTHON),python3) scripts/validate_formula.py --part $(PART) --params $(PARAMS) --steps $(STEPS)

# Validate formula with multi-view PNG generation
validate-formula-png:
	@$(or $(PYTHON),python3) scripts/validate_formula.py --part $(PART) --params $(PARAMS) --steps $(STEPS) --render-png
