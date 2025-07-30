# Testing Guide

## Overview

ScannerProxy includes a comprehensive testing framework with 90%+ test coverage. This guide covers testing strategies, running tests, and understanding test results.

## Test Structure

```
tests/
├── unit/                    # Unit tests (isolated component testing)
│   ├── test_config.py          # Configuration management tests
│   ├── test_scanner_service.py # Main service logic tests
│   ├── test_network_models.py  # Data model validation tests
│   ├── test_discovery.py       # Network discovery tests
│   ├── test_network_interfaces.py # Network interface tests
│   ├── test_message_protocols.py  # Protocol handling tests
│   └── test_file_transfer.py   # File transfer service tests
├── integration/             # Integration tests (end-to-end workflows)
├── mocks/                   # Mock implementations for testing
│   └── mock_scanner.py      # Scanner simulation for manual testing
└── conftest.py             # Test configuration and fixtures
```

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test categories
make test-unit
make test-integration
```

### Detailed Test Commands

#### Basic Test Execution
```bash
# All tests with verbose output
make test

# Unit tests only (faster, isolated)
make test-unit

# Integration tests only (slower, end-to-end)
make test-integration

# Watch mode (re-run tests on file changes)
make test-watch
```

#### Coverage Analysis
```bash
# Generate HTML and terminal coverage reports
make test-coverage

# Generate XML coverage report (for CI/CD)
make test-coverage-xml

# View HTML coverage report
open htmlcov/index.html
```

#### Component-Specific Tests
```bash
# Configuration management
make test-config

# Scanner service business logic
make test-scanner

# Network operations (discovery, interfaces)
make test-network

# Message protocol handling
make test-protocols

# File transfer operations
make test-file-transfer
```

### Direct pytest Commands

```bash
# Run specific test file
pytest tests/unit/test_config.py -v

# Run specific test method
pytest tests/unit/test_config.py::TestConfigurationManager::test_load_config_success -v

# Run tests matching pattern
pytest -k "test_config" -v

# Run tests with coverage
pytest --cov=src --cov-report=html tests/

# Run tests in parallel (if pytest-xdist is installed)
pytest -n auto tests/
```

## Test Categories

### Unit Tests

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (< 1 second per test)
- Isolated from external dependencies
- Comprehensive mocking of dependencies
- High coverage of edge cases and error conditions

**Examples**:
```python
def test_config_loading_success():
    """Test successful configuration loading"""
    # Arrange: Set up mocks and test data
    # Act: Call the method under test
    # Assert: Verify expected behavior
```

### Integration Tests

**Purpose**: Test component interactions and end-to-end workflows

**Characteristics**:
- Slower execution (multiple seconds)
- Test real component interactions
- Minimal mocking (only external services)
- Focus on workflow validation

**Examples**:
```python
def test_complete_discovery_workflow():
    """Test full agent discovery process"""
    # Test actual network discovery with mock agents
```

### Mock Tests

**Purpose**: Test with simulated external services

**Usage**:
```bash
# Run mock scanner for manual testing
python tests/mocks/mock_scanner.py
```

## Test Configuration

### pytest.ini

The project uses pytest configuration for consistent test execution:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (> 1 second)
```

### conftest.py

Shared test fixtures and configuration:

```python
@pytest.fixture
def sample_protocol_message():
    """Provide a sample protocol message for testing"""
    return ScannerProtocolMessage(...)

@pytest.fixture
def mock_network_interface():
    """Mock network interface for testing"""
    with patch('src.network.interfaces.netifaces') as mock:
        yield mock
```

## Coverage Analysis

### Understanding Coverage Reports

#### Terminal Output
```
Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
src/core/scanner_service.py          45      2    96%   23, 67
src/network/discovery.py             38      1    97%   89
src/utils/config.py                   32      0   100%
----------------------------------------------------------------
TOTAL                               234      8    97%
```

**Metrics**:
- **Stmts**: Total statements in the file
- **Miss**: Statements not covered by tests
- **Cover**: Percentage of statements covered
- **Missing**: Line numbers not covered

#### HTML Coverage Report

Open `htmlcov/index.html` to see:
- Interactive coverage visualization
- Line-by-line coverage highlighting
- Missing line identification
- Branch coverage analysis

### Coverage Goals

- **Overall Target**: 90%+ coverage
- **Critical Components**: 95%+ coverage
  - Configuration management
  - Network discovery
  - Message protocols
- **Acceptable Lower Coverage**: 85%+ for utility functions

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_method_name_scenario():
    """Clear description of what is being tested"""
    # Arrange: Set up test data and mocks
    mock_dependency = Mock()
    test_input = "test_value"
    
    # Act: Execute the method under test
    result = method_under_test(test_input, dependency=mock_dependency)
    
    # Assert: Verify expected outcomes
    assert result == expected_value
    mock_dependency.method.assert_called_once_with(test_input)
```

### Mocking Guidelines

#### Patch External Dependencies
```python
@patch('src.network.interfaces.netifaces.interfaces')
def test_network_interface_detection(mock_interfaces):
    mock_interfaces.return_value = ['eth0', 'lo']
    # Test network interface detection logic
```

#### Mock Configuration
```python
@patch.object(ConfigurationManager, 'load_config')
def test_config_dependent_method(mock_load_config):
    mock_load_config.return_value = {'test': 'value'}
    # Test method that depends on configuration
```

#### Mock Network Operations
```python
@patch('socket.socket')
def test_network_communication(mock_socket):
    mock_socket.return_value.recvfrom.return_value = (b'data', ('127.0.0.1', 8080))
    # Test network communication logic
```

### Test Data Management

#### Use Fixtures for Reusable Data
```python
@pytest.fixture
def sample_network_config():
    return {
        'udp_port': 706,
        'tcp_port': 708,
        'discovery_timeout': 10.0
    }
```

#### Create Builders for Complex Objects
```python
class ProtocolMessageBuilder:
    def __init__(self):
        self.message = ScannerProtocolMessage()
    
    def with_ip(self, ip):
        self.message.initiator_ip = IPv4Address(ip)
        return self
    
    def build(self):
        return self.message
```

### Error Testing

#### Test Exception Handling
```python
def test_config_load_with_invalid_yaml():
    with patch('builtins.open', mock_open(read_data="invalid: yaml: content:")):
        with pytest.raises(yaml.YAMLError):
            config_manager.load_config()
```

#### Test Edge Cases
```python
def test_discovery_with_zero_timeout():
    """Test discovery behavior with zero timeout"""
    agents = discovery_service.discover_agents(timeout=0)
    assert agents == []
```

## Continuous Integration

### CI Test Pipeline

```bash
# Install dependencies
make install-test-deps

# Run full test suite with coverage
make ci-test

# Generate coverage reports
make test-coverage-xml
```

### Pre-commit Hooks

```bash
# Run all pre-commit checks
make pre-commit

# Individual checks
make format
make lint
make test
```

## Troubleshooting

### Common Test Issues

#### Import Errors
```bash
# Ensure proper Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use module execution
python -m pytest tests/
```

#### Mock Issues
```python
# Ensure mocking the correct target
# Wrong: @patch('module.function')
# Right: @patch('src.module.function')

# Ensure mock is configured before use
mock_object.return_value = expected_value
```

#### Coverage Issues
```bash
# Clean previous coverage data
rm .coverage

# Run coverage with fresh start
make test-coverage
```

### Test Performance

#### Slow Tests
```bash
# Run only fast tests
pytest -m "not slow"

# Profile test execution
pytest --durations=10
```

#### Memory Issues
```bash
# Run tests with memory profiling
pytest --memmon

# Limit parallel test execution
pytest -n 2  # Instead of -n auto
```

## Best Practices

### Test Organization
- One test file per source module
- Group related tests in classes
- Use descriptive test names
- Keep tests independent and isolated

### Test Quality
- Test both success and failure paths
- Include edge cases and boundary conditions
- Use meaningful assertions
- Avoid testing implementation details

### Maintenance
- Update tests when code changes
- Remove obsolete tests
- Refactor test code for clarity
- Monitor coverage trends

### Performance
- Keep unit tests fast (< 100ms)
- Use mocks to avoid slow operations
- Group slow tests separately
- Run subset of tests during development

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
