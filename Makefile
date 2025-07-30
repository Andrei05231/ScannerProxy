# Variables
IMAGE_NAME = scannerproxy
CONTAINER_NAME = scannerproxy
NETWORK_NAME = scannerproxy_ipvlan-net
PORT = 8000
TEST_IP_ADDRESS = 10.0.52.222

# Create local development environment
venv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt

# Build the Docker test image
build-test:
	docker build -f Dockerfile.test -t $(IMAGE_NAME)-test1:latest .

# Run the Docker test container
run-test:
	docker run -it --rm --cap-add=NET_ADMIN --name $(CONTAINER_NAME)-test1 --network $(NETWORK_NAME) --ip $(TEST_IP_ADDRESS) $(IMAGE_NAME)-test1:latest

run-test-debug:
	docker run -it --rm --cap-add=NET_ADMIN --entrypoint /bin/bash --name $(CONTAINER_NAME)-test1 --network $(NETWORK_NAME) --ip $(TEST_IP_ADDRESS) $(IMAGE_NAME)-test1:latest

local-server:
	CONT_IP=127.0.0.1 DEV_NAME=Custom-Scn1 DESTINATION=scan1 venv/bin/python app/connectToScanner.py

local-client:
	CONT_IP=127.0.0.1 DEV_NAME=Custom-Scn1-test DESTINATION=scan1 venv/bin/python app/testReceiver.py



.PHONY: build-test run-test run-test-debug local-server local-client venv