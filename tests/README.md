# Testing Documentation

## Overview

This directory contains a comprehensive test suite for the Creative Automation Pipeline, covering unit tests, integration tests, and end-to-end tests. The test suite is built with pytest and includes mocked external API calls to ensure fast, reliable, and cost-effective testing.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_data/              # Sample data for testing
│   ├── sample_brief.yaml
│   ├── sample_brief_invalid.yaml
│   ├── sample_brief_noncompliant.yaml
│   └── test_image*.jpg     # Generated test images
├── unit/                   # Unit tests for individual components
│   ├── test_compliance_agent.py
│   ├── test_image_generator.py
│   ├── test_storage_manager.py
│   ├── test_creative_engine.py
│   ├── test_orchestrator.py
│   └── test_config.py
├── integration/            # Integration tests for component interactions
│   ├── test_api_endpoints.py
│   ├── test_campaign_workflow.py
│   └── test_storage_modes.py
└── e2e/                    # End-to-end tests
    └── test_full_campaign.py
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Or with uv
uv pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit -m unit

# Integration tests only
pytest tests/integration -m integration

# End-to-end tests only
pytest tests/e2e -m e2e

# Local storage tests only
pytest -m local

# Dropbox storage tests only
pytest -m dropbox

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Single file
pytest tests/unit/test_compliance_agent.py

# Single test class
pytest tests/unit/test_compliance_agent.py::TestComplianceAgent

# Single test function
pytest tests/unit/test_compliance_agent.py::TestComplianceAgent::test_initialization
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Open HTML coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
# See all test names and outputs
pytest -v -s

# Even more verbose
pytest -vv
```

## Test Markers

The test suite uses pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.e2e` - End-to-end tests for complete workflows
- `@pytest.mark.local` - Tests specific to local storage mode
- `@pytest.mark.dropbox` - Tests specific to Dropbox storage mode
- `@pytest.mark.slow` - Slow-running tests (typically E2E tests)

## Mocking Strategy

### Gemini API Mocking

All Gemini API calls are mocked to avoid:
- API usage costs during testing
- Dependency on external services
- Non-deterministic test results
- Slow test execution


### Dropbox API Mocking

Dropbox operations are mocked to test both storage modes without requiring actual Dropbox credentials:

## Fixtures

### Core Fixtures (conftest.py)

- `mock_env_vars` - Sets test environment variables
- `mock_env_no_dropbox` - Environment without Dropbox credentials
- `temp_storage` - Temporary directory structure for testing
- `sample_image` - Basic test image (square)
- `sample_image_portrait` - Portrait test image (9:16)
- `sample_image_landscape` - Landscape test image (16:9)
- `sample_brief` - Valid campaign brief
- `sample_brief_invalid` - Invalid campaign brief (missing fields)
- `sample_brief_noncompliant` - Non-compliant campaign brief

### Component Fixtures

- `mock_config` - Configured AppConfig for testing
- `mock_config_with_dropbox` - AppConfig with Dropbox credentials
- `compliance_agent` - Initialized ComplianceAgent
- `image_generator` - Initialized ImageGenerator
- `creative_engine` - Initialized CreativeEngine
- `storage_manager_local` - StorageManager in local mode
- `storage_manager_dropbox` - StorageManager in Dropbox mode
- `orchestrator` - Full CampaignOrchestrator

### API Fixtures

- `fastapi_test_client` - FastAPI TestClient for API testing
- `log_callback` - Mock logging callback function

## Test Coverage Goals

- **Overall Coverage:** 80%+
- **Critical Components:** 90%+
  - CampaignOrchestrator
  - ComplianceAgent
  - StorageManager

### Checking Coverage

```bash
# Run tests with coverage
uv run pytest --cov=. --cov-report=term-missing --cov-report=html

# View detailed coverage report
open htmlcov/index.html
```

Coverage reports show:
- Lines of code tested
- Missing coverage (untested lines)
- Branch coverage
- Per-file coverage statistics

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

