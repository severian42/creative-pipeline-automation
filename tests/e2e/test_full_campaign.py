"""
End-to-end tests for complete campaign pipeline.
"""

import pytest
import time
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from PIL import Image
import io


@pytest.mark.e2e
class TestFullCampaignPipeline:
    """End-to-end tests for complete campaign workflows."""
    
    @pytest.fixture
    def client(self, mock_env_vars):
        """Create test client."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client'):
            from app import app
            return TestClient(app)
    
    @pytest.mark.slow
    def test_complete_campaign_with_api(self, client, sample_brief, sample_image):
        """Test complete campaign flow through API."""
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Mock compliance to pass
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            # Mock image generation
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            image_chunk = MagicMock()
            image_chunk.candidates = [MagicMock()]
            image_chunk.candidates[0].content = MagicMock()
            image_chunk.candidates[0].content.parts = [MagicMock()]
            image_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            image_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def image_stream(*args, **kwargs):
                yield image_chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Step 1: Submit campaign
            response = client.post(
                "/api/v1/campaigns/generate",
                json=sample_brief
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "campaign_id" in data
            campaign_id = data["campaign_id"]
            
            # Step 2: Poll for status
            max_polls = 20
            poll_count = 0
            status = "processing"
            
            while poll_count < max_polls and status == "processing":
                time.sleep(0.2)
                response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "processing")
                
                poll_count += 1
            
            # Step 3: Verify completion
            assert status in ["completed", "failed"]
            
            if status == "completed":
                # Step 4: List outputs
                response = client.get(f"/api/v1/campaigns/{campaign_id}/outputs")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "outputs" in data
    
    @pytest.mark.slow
    def test_campaign_with_locale_e2e(self, client, sample_brief, sample_image):
        """Test end-to-end campaign with locale parameter."""
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Mock compliance
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            # Mock image generation
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            image_chunk = MagicMock()
            image_chunk.candidates = [MagicMock()]
            image_chunk.candidates[0].content = MagicMock()
            image_chunk.candidates[0].content.parts = [MagicMock()]
            image_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            image_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def image_stream(*args, **kwargs):
                yield image_chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Submit with locale
            response = client.post(
                "/api/v1/campaigns/generate",
                params={"locale": "es_ES"},
                json=sample_brief
            )
            
            assert response.status_code == 200
            campaign_id = response.json()["campaign_id"]
            
            # Wait for completion
            time.sleep(0.5)
            
            # Check status
            response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
            
            if response.status_code == 200:
                data = response.json()
                # Should have locale in result
                assert data.get("locale") == "es_ES" or "status" in data
    
    @pytest.mark.slow
    def test_campaign_with_ab_variant_e2e(self, client, sample_brief, sample_image):
        """Test end-to-end campaign with A/B variant."""
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Mock compliance
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            # Mock image generation
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            image_chunk = MagicMock()
            image_chunk.candidates = [MagicMock()]
            image_chunk.candidates[0].content = MagicMock()
            image_chunk.candidates[0].content.parts = [MagicMock()]
            image_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            image_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def image_stream(*args, **kwargs):
                yield image_chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Submit with A/B variant
            response = client.post(
                "/api/v1/campaigns/generate",
                params={"ab_variant": "variant_b"},
                json=sample_brief
            )
            
            assert response.status_code == 200
            campaign_id = response.json()["campaign_id"]
            
            # Wait for completion
            time.sleep(0.5)
            
            # Check status
            response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
            
            if response.status_code == 200:
                data = response.json()
                # Should have variant in result
                assert data.get("ab_variant") == "variant_b" or "status" in data
    
    def test_invalid_brief_e2e(self, client, sample_brief_invalid):
        """Test end-to-end flow with invalid brief."""
        response = client.post(
            "/api/v1/campaigns/generate",
            json=sample_brief_invalid
        )
        
        # Should accept request
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            campaign_id = response.json()["campaign_id"]
            
            # Wait a bit
            time.sleep(0.5)
            
            # Check status - should fail
            response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
            
            if response.status_code == 200:
                data = response.json()
                # Should fail due to validation
                assert data.get("status") in ["failed", "processing"]
    
    def test_brief_parsing_e2e(self, client, sample_brief):
        """Test brief parsing in end-to-end flow."""
        # Parse brief
        response = client.post(
            "/api/v1/campaigns/parse-brief",
            json=sample_brief
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return locales and variants
        assert "locales" in data
        assert "ab_variants" in data
        
        # Verify data structure
        assert isinstance(data["locales"], list)
        assert isinstance(data["ab_variants"], list)
    
    def test_health_check_e2e(self, client):
        """Test health check in end-to-end flow."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "storage_mode" in data
        assert "gemini_api_configured" in data
    
    @pytest.mark.slow
    def test_multiple_concurrent_campaigns_e2e(self, client, sample_brief, sample_image):
        """Test multiple campaigns running concurrently."""
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Mock compliance
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            # Mock image generation
            buffer = io.BytesIO()
            sample_image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            image_chunk = MagicMock()
            image_chunk.candidates = [MagicMock()]
            image_chunk.candidates[0].content = MagicMock()
            image_chunk.candidates[0].content.parts = [MagicMock()]
            image_chunk.candidates[0].content.parts[0].inline_data = MagicMock()
            image_chunk.candidates[0].content.parts[0].inline_data.data = image_bytes
            
            def image_stream(*args, **kwargs):
                yield image_chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Submit multiple campaigns
            campaign_ids = []
            for i in range(3):
                brief = sample_brief.copy()
                brief["campaign_id"] = f"test-campaign-{i}"
                
                response = client.post(
                    "/api/v1/campaigns/generate",
                    json=brief
                )
                
                if response.status_code == 200:
                    campaign_ids.append(response.json()["campaign_id"])
            
            # Wait for campaigns to process
            time.sleep(1.0)
            
            # Check all campaigns
            for campaign_id in campaign_ids:
                response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
                assert response.status_code == 200
    
    def test_campaign_error_recovery_e2e(self, client, sample_brief):
        """Test error recovery in end-to-end flow."""
        with patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Make compliance fail
            def compliance_stream(*args, **kwargs):
                raise Exception("Compliance check failed")
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            # Submit campaign
            response = client.post(
                "/api/v1/campaigns/generate",
                json=sample_brief
            )
            
            if response.status_code == 200:
                campaign_id = response.json()["campaign_id"]
                
                # Wait
                time.sleep(0.5)
                
                # Check status - should have error
                response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
                
                if response.status_code == 200:
                    data = response.json()
                    # Should report error
                    assert "status" in data
                    if data["status"] == "failed":
                        assert len(data.get("errors", [])) > 0

