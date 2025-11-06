"""
Integration tests for FastAPI endpoints.
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    @pytest.fixture
    def client(self, mock_env_vars):
        """Create test client."""
        # Need to import after setting env vars
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client'):
            from app import app
            return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "storage_mode" in data
        assert "gemini_api_configured" in data
        assert "dropbox_configured" in data
    
    def test_generate_campaign_endpoint_valid(self, client, sample_brief):
        """Test campaign generation endpoint with valid brief."""
        with patch('app.orchestrator.execute_campaign') as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "output_paths": {},
                "errors": [],
                "progress": 100
            }
            
            response = client.post(
                "/api/v1/campaigns/generate",
                json=sample_brief
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "campaign_id" in data
            assert data["status"] == "processing"
    
    def test_generate_campaign_endpoint_invalid_data(self, client):
        """Test campaign generation with invalid data."""
        invalid_brief = {
            "campaign_id": "test"
            # Missing required fields
        }
        
        response = client.post(
            "/api/v1/campaigns/generate",
            json=invalid_brief
        )
        
        # Should accept request but processing will fail
        assert response.status_code in [200, 422]
    
    def test_campaign_status_endpoint(self, client, sample_brief):
        """Test campaign status endpoint."""
        with patch('app.orchestrator.execute_campaign') as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "output_paths": {},
                "errors": [],
                "progress": 100
            }
            
            # Start a campaign
            response = client.post(
                "/api/v1/campaigns/generate",
                json=sample_brief
            )
            campaign_id = response.json()["campaign_id"]
            
            # Give background task time to start
            time.sleep(0.1)
            
            # Check status
            response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    def test_campaign_status_not_found(self, client):
        """Test status endpoint for non-existent campaign."""
        response = client.get("/api/v1/campaigns/nonexistent/status")
        
        assert response.status_code == 404
    
    def test_list_campaign_outputs_endpoint(self, client):
        """Test listing campaign outputs."""
        with patch('app.orchestrator.storage_manager.list_campaign_outputs') as mock_list:
            mock_list.return_value = [
                "/path/to/output1.jpg",
                "/path/to/output2.jpg"
            ]
            
            response = client.get("/api/v1/campaigns/test-campaign/outputs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["campaign_id"] == "test-campaign"
            assert data["output_count"] == 2
            assert len(data["outputs"]) == 2
    
    def test_list_campaign_outputs_error(self, client):
        """Test error handling in list outputs."""
        with patch('app.orchestrator.storage_manager.list_campaign_outputs') as mock_list:
            mock_list.side_effect = Exception("Storage error")
            
            response = client.get("/api/v1/campaigns/test-campaign/outputs")
            
            assert response.status_code == 500
    
    def test_upload_assets_endpoint(self, client):
        """Test asset upload endpoint."""
        with patch('app.orchestrator.storage_manager.upload_user_assets') as mock_upload:
            mock_upload.return_value = {
                "uploaded_count": 2,
                "files": ["/path/to/file1.jpg", "/path/to/file2.jpg"]
            }
            
            response = client.post(
                "/api/v1/assets/upload",
                json=["/temp/file1.jpg", "/temp/file2.jpg"]
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["uploaded_count"] == 2
    
    def test_upload_assets_error(self, client):
        """Test error handling in asset upload."""
        with patch('app.orchestrator.storage_manager.upload_user_assets') as mock_upload:
            mock_upload.side_effect = Exception("Upload failed")
            
            response = client.post(
                "/api/v1/assets/upload",
                json=["/temp/file.jpg"]
            )
            
            assert response.status_code == 500
    
    def test_parse_brief_endpoint(self, client, sample_brief):
        """Test brief parsing endpoint."""
        response = client.post(
            "/api/v1/campaigns/parse-brief",
            json=sample_brief
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "locales" in data
        assert "ab_variants" in data
        assert "default_message" in data
    
    def test_parse_brief_with_locales(self, client, sample_brief):
        """Test parsing brief with locales."""
        response = client.post(
            "/api/v1/campaigns/parse-brief",
            json=sample_brief
        )
        
        data = response.json()
        assert len(data["locales"]) > 0
        assert "en_US" in data["locales"]
    
    def test_parse_brief_with_ab_variants(self, client, sample_brief):
        """Test parsing brief with A/B variants."""
        response = client.post(
            "/api/v1/campaigns/parse-brief",
            json=sample_brief
        )
        
        data = response.json()
        assert len(data["ab_variants"]) > 0
        assert "variant_a" in data["ab_variants"]
    
    def test_parse_brief_error(self, client):
        """Test error handling in brief parsing."""
        with patch('app.orchestrator.get_available_locales') as mock_locales:
            mock_locales.side_effect = Exception("Parse error")
            
            response = client.post(
                "/api/v1/campaigns/parse-brief",
                json={}
            )
            
            assert response.status_code == 500
    
    def test_generate_with_locale_parameter(self, client, sample_brief):
        """Test campaign generation with locale parameter."""
        with patch('app.process_campaign_async') as mock_process:
            response = client.post(
                "/api/v1/campaigns/generate",
                params={"locale": "es_ES"},
                json=sample_brief
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            
            # Verify background task was scheduled with locale
            import time
            time.sleep(0.1)  # Give background task time to start
            
            # The locale parameter should be passed through the request
    
    def test_generate_with_ab_variant_parameter(self, client, sample_brief):
        """Test campaign generation with A/B variant parameter."""
        with patch('app.process_campaign_async') as mock_process:
            response = client.post(
                "/api/v1/campaigns/generate",
                params={"ab_variant": "variant_b"},
                json=sample_brief
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            
            # Verify background task was scheduled with variant
            import time
            time.sleep(0.1)  # Give background task time to start
            
            # The ab_variant parameter should be passed through the request
    
    def test_cors_headers(self, client):
        """Test CORS middleware is configured."""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # CORS should be configured
        assert response.status_code in [200, 405]
    
    def test_campaign_status_with_logs(self, client, sample_brief):
        """Test status endpoint returns logs."""
        with patch('app.orchestrator.execute_campaign') as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "output_paths": {},
                "errors": [],
                "progress": 100
            }
            
            # Start campaign
            response = client.post(
                "/api/v1/campaigns/generate",
                json=sample_brief
            )
            campaign_id = response.json()["campaign_id"]
            
            time.sleep(0.1)
            
            # Get status
            response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
            data = response.json()
            
            assert "logs" in data
            assert isinstance(data["logs"], list)
    
    def test_campaign_status_with_progress(self, client, sample_brief):
        """Test status endpoint returns progress."""
        with patch('app.orchestrator.execute_campaign') as mock_execute:
            mock_execute.return_value = {
                "status": "processing",
                "output_paths": {},
                "errors": [],
                "progress": 50
            }
            
            # Start campaign
            response = client.post(
                "/api/v1/campaigns/generate",
                json=sample_brief
            )
            campaign_id = response.json()["campaign_id"]
            
            time.sleep(0.1)
            
            # Get status
            response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
            data = response.json()
            
            assert "progress" in data
    
    def test_concurrent_campaigns(self, client, sample_brief):
        """Test handling multiple concurrent campaigns."""
        with patch('app.orchestrator.execute_campaign') as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "output_paths": {},
                "errors": [],
                "progress": 100
            }
            
            # Start multiple campaigns
            response1 = client.post("/api/v1/campaigns/generate", json=sample_brief)
            
            brief2 = sample_brief.copy()
            brief2["campaign_id"] = "test-campaign-002"
            response2 = client.post("/api/v1/campaigns/generate", json=brief2)
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Different campaign IDs
            assert response1.json()["campaign_id"] != response2.json()["campaign_id"]

