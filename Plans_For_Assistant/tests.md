Create a production-ready test suite covering all components with unit tests, integration tests, and end-to-end workflows. Mock Gemini API calls to avoid costs and ensure reproducibility while testing both local and Dropbox storage modes.
Test Structure
Directory Layout
backend/

├── tests/

│   ├── __init__.py

│   ├── conftest.py                  # Shared fixtures

│   ├── test_data/                   # Mock data

│   │   ├── sample_brief.yaml

│   │   ├── sample_brief_invalid.yaml

│   │   ├── test_image.jpg

│   │   └── test_image_portrait.jpg

│   ├── unit/

│   │   ├── __init__.py

│   │   ├── test_compliance_agent.py

│   │   ├── test_image_generator.py

│   │   ├── test_storage_manager.py

│   │   ├── test_creative_engine.py

│   │   ├── test_orchestrator.py

│   │   └── test_config.py

│   ├── integration/

│   │   ├── __init__.py

│   │   ├── test_api_endpoints.py

│   │   ├── test_campaign_workflow.py

│   │   └── test_storage_modes.py

│   └── e2e/

│       ├── __init__.py

│       └── test_full_campaign.py

├── pytest.ini

└── .env.test
Component Testing Breakdown
1. ComplianceAgent Tests (test_compliance_agent.py)
Legal compliance checks
Valid messages pass
Discriminatory language detected
Harmful content flagged
Edge cases (empty, very long messages)
Brand compliance checks
Patagonia values alignment
Forbidden terms detection ("buy now", "guaranteed", etc.)
Brand voice validation
Auto-fix functionality
Single fix attempts
Multiple retry scenarios
Fix success/failure paths
Max attempts exhaustion
Multi-language support
English, Spanish, French messages
Locale-specific compliance
Error handling
JSON parsing failures
API timeouts
Invalid responses
2. ImageGenerator Tests (test_image_generator.py)
Image generation
All aspect ratios (1:1, 9:16, 16:9)
Valid PIL Image output
Correct dimensions
Locale support
Different language contexts
Language hints in prompts
Error handling
API failures
Invalid aspect ratios
Empty responses
Mock Gemini API
Return pre-generated test images
Simulate API errors
Test streaming responses
3. StorageManager Tests (test_storage_manager.py)
Local storage mode
Asset finding (existing/missing)
Creative uploads
Directory creation
File listing
Dropbox storage mode
Connection initialization
Asset retrieval
File uploads
Path normalization
Folder creation
Error handling (auth failures, quota)
Mode switching
Credential detection
Fallback to local
Asset operations
Find by filename
Multiple file formats (jpg, png, webp)
User asset uploads
4. CreativeEngine Tests (test_creative_engine.py)
Image resizing
All aspect ratios
Crop centering
Quality preservation
Text overlay
Message rendering
Product name placement
Font loading (with fallbacks)
Text wrapping
Responsive sizing
Complete processing
Resize + overlay pipeline
Various image sizes
Edge cases (very long text, small images)
5. CampaignOrchestrator Tests (test_orchestrator.py)
Workflow execution
Complete campaign flow
Product processing
Progress tracking
Locale handling
Message selection by locale
Multi-language campaigns
A/B variant handling
Variant message selection
Default fallback
Error handling
Missing fields
Insufficient products
Component failures
Logging callbacks
Message propagation
Progress updates
6. Config Tests (test_config.py)
Environment loading
Valid configurations
Missing required vars
Optional var handling
Credential detection
Dropbox access token
Refresh token flow
No credentials
Storage mode determination
Dropbox mode selection
Local mode fallback
Brand guidelines access
Data structure validation
Completeness
7. API Endpoint Tests (test_api_endpoints.py)
Health check endpoint
Status response
Configuration info
Campaign generation
Valid brief submission
Invalid data rejection
Background task execution
Status polling
Campaign tracking
404 for missing campaigns
Progress updates
Output listing
File retrieval
Empty campaigns
Brief parsing
Locale extraction
A/B variant extraction
Asset upload
Multiple files
Error handling
8. Integration Tests
Campaign Workflow (test_campaign_workflow.py)
End-to-end scenarios
With existing assets
With generated images
With compliance fixes
Multi-product campaigns
Locale variations
Spanish campaign
French campaign
A/B testing
Variant A vs B execution
Storage Modes (test_storage_modes.py)
Local-to-Dropbox transitions
Mode switching
Data consistency
Parallel operations
Concurrent uploads
Race conditions
9. E2E Tests (test_full_campaign.py)
Complete pipeline
API call → Processing → Output
Status polling loop
File verification
Error scenarios
Invalid briefs
Missing assets
API failures
Test Infrastructure
Fixtures (conftest.py)
# Core fixtures

- mock_config: Test configuration

- mock_gemini_client: Mocked Gemini API

- temp_storage: Temporary directories

- sample_image: Test PIL Image

- sample_brief: Valid campaign brief

- mock_dropbox: Mocked Dropbox client

# Component fixtures

- compliance_agent: Initialized agent

- image_generator: Initialized generator

- storage_manager_local: Local mode

- storage_manager_dropbox: Dropbox mode

- creative_engine: Initialized engine

- orchestrator: Full orchestrator

# API fixtures

- test_client: FastAPI test client

- mock_background_tasks: Background task mock
Mock Data
Sample briefs: Valid, invalid, minimal, complete
Test images: Various sizes and aspect ratios
Expected outputs: Reference creatives for comparison
Mocking Strategy
Gemini API: Mock with unittest.mock or responses library
Dropbox API: Mock with dropbox test fixtures
File system: Use tmp_path pytest fixture
Background tasks: Mock FastAPI BackgroundTasks
Test Configuration
pytest.ini
[pytest]

testpaths = tests

python_files = test_*.py

python_classes = Test*

python_functions = test_*

addopts = 

    -v

    --tb=short

    --strict-markers

    --cov=.

    --cov-report=html

    --cov-report=term-missing

    --cov-fail-under=80

markers =

    unit: Unit tests

    integration: Integration tests

    e2e: End-to-end tests

    local: Local storage tests

    dropbox: Dropbox storage tests

    slow: Slow-running tests
.env.test
GEMINI_API_KEY=test_key_12345

DROPBOX_ACCESS_TOKEN=test_token_12345

DROPBOX_BASE_PATH=/test
Coverage Requirements
Target: 80%+ overall coverage
Critical paths: 90%+ (orchestrator, compliance)
Report formats: HTML + terminal
Exclusions: External API calls, UI rendering
Implementation Steps
Setup test infrastructure

Create test directory structure
Install pytest and dependencies
Configure pytest.ini and .env.test

Create fixtures and mocks

Build conftest.py with shared fixtures
Create mock Gemini API responses
Setup Dropbox mocks

Generate test data

Create sample YAML briefs
Generate test images (various sizes)
Prepare expected outputs

Write unit tests

Test each module independently
Cover all public methods
Test error paths

Write integration tests

Test component interactions
Test both storage modes
Test API endpoints

Write E2E tests

Full campaign workflows
Real-world scenarios

Add test documentation

Document test strategy
Explain mock setup
Provide run instructions

Verify coverage

Run coverage reports
Identify gaps
Add missing tests
Running Tests
# All tests

pytest

# Unit tests only

pytest tests/unit -m unit

# Integration tests

pytest tests/integration -m integration

# Specific component

pytest tests/unit/test_compliance_agent.py

# With coverage

pytest --cov=. --cov-report=html

# Local storage tests only

pytest -m local

# Dropbox tests only

pytest -m dropbox

# Verbose with output

pytest -v -s
Key Files to Create
tests/conftest.py - Shared fixtures
tests/test_data/sample_brief.yaml - Test campaign
8 unit test files (one per module)
3 integration test files
1 E2E test file
pytest.ini - Test configuration
.env.test - Test environment
requirements-test.txt - Test dependencies
Dependencies to Add
pytest

pytest-asyncio

pytest-cov

pytest-mock

responses

httpx

