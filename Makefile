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

# Install test dependencies
install-test-deps:
	pip install pytest pytest-cov pytest-mock pytest-asyncio coverage

# Run all tests
test:
	python -m pytest tests/ -v

# Run unit tests only
test-unit:
	python -m pytest tests/unit/ -v

# Run integration tests only
test-integration:
	python -m pytest tests/integration/ -v

# Run tests with coverage report
test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

# Run tests with coverage and generate XML report (for CI)
test-coverage-xml:
	python -m pytest tests/ --cov=src --cov-report=xml --cov-report=term-missing -v

# Run specific test file
test-config:
	python -m pytest tests/unit/test_config.py -v

test-scanner:
	python -m pytest tests/unit/test_scanner_service.py -v

test-network:
	python -m pytest tests/unit/test_network_models.py tests/unit/test_discovery.py tests/unit/test_network_interfaces.py -v

test-protocols:
	python -m pytest tests/unit/test_message_protocols.py -v

test-file-transfer:
	python -m pytest tests/unit/test_file_transfer.py -v

# Run tests in watch mode (requires pytest-watch)
test-watch:
	ptw tests/ -- -v

# Clean all artifacts (tests + build)
clean: clean-test clean-build

# Clean test artifacts
clean-test:
	-rm -rf .pytest_cache/
	-rm -rf htmlcov/
	-rm -f coverage.xml
	-rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Clean build artifacts
clean-build:
	-rm -rf build/
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .tox/
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

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

.PHONY: build-test run-test run-test-debug local-server local-client venv install-test-deps test test-unit test-integration test-coverage test-coverage-xml test-config test-scanner test-network test-protocols test-file-transfer test-watch clean clean-test clean-build