"""
Unit tests for CampaignOrchestrator.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from modules.orchestrator import CampaignOrchestrator


@pytest.mark.unit
class TestCampaignOrchestrator:
    """Test suite for CampaignOrchestrator."""
    
    def test_initialization(self, mock_config):
        """Test CampaignOrchestrator initializes with all components."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client'):
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            assert orchestrator.config == mock_config
            assert orchestrator.storage_manager is not None
            assert orchestrator.image_generator is not None
            assert orchestrator.creative_engine is not None
            assert orchestrator.compliance_agent is not None
    
    def test_get_campaign_message_default(self, orchestrator):
        """Test getting default campaign message."""
        brief = {
            "campaign_message": "Default message"
        }
        
        message = orchestrator._get_campaign_message(brief)
        
        assert message == "Default message"
    
    def test_get_campaign_message_with_locale(self, orchestrator):
        """Test getting locale-specific campaign message."""
        brief = {
            "campaign_message": "Default message",
            "locales": [
                {
                    "language": "es",
                    "region": "ES",
                    "message": "Mensaje en español"
                },
                {
                    "language": "fr",
                    "region": "FR",
                    "message": "Message en français"
                }
            ]
        }
        
        message = orchestrator._get_campaign_message(brief, locale="es_ES")
        
        assert message == "Mensaje en español"
    
    def test_get_campaign_message_with_ab_variant(self, orchestrator):
        """Test getting A/B variant campaign message."""
        brief = {
            "campaign_message": "Default message",
            "ab_testing": {
                "enabled": True,
                "variants": [
                    {
                        "name": "variant_a",
                        "message": "Variant A message"
                    },
                    {
                        "name": "variant_b",
                        "message": "Variant B message"
                    }
                ]
            }
        }
        
        message = orchestrator._get_campaign_message(brief, ab_variant="variant_b")
        
        assert message == "Variant B message"
    
    def test_get_available_locales(self, orchestrator, sample_brief):
        """Test getting list of available locales."""
        locales = orchestrator.get_available_locales(sample_brief)
        
        assert len(locales) > 0
        assert "en_US" in locales
        assert "es_ES" in locales
        assert "fr_FR" in locales
    
    def test_get_available_ab_variants(self, orchestrator, sample_brief):
        """Test getting list of available A/B variants."""
        variants = orchestrator.get_available_ab_variants(sample_brief)
        
        assert len(variants) > 0
        assert "variant_a" in variants
        assert "variant_b" in variants
    
    def test_get_available_ab_variants_disabled(self, orchestrator):
        """Test getting A/B variants when disabled."""
        brief = {
            "ab_testing": {
                "enabled": False
            }
        }
        
        variants = orchestrator.get_available_ab_variants(brief)
        
        assert variants == []
    
    def test_execute_campaign_validates_required_fields(self, mock_config):
        """Test that execute_campaign validates required fields."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client'):
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Missing required fields
            invalid_brief = {
                "campaign_id": "test"
                # Missing other required fields
            }
            
            result = orchestrator.execute_campaign(invalid_brief)
            
            assert result['status'] == 'failed'
            assert len(result['errors']) > 0
    
    def test_execute_campaign_validates_product_count(self, mock_config):
        """Test that execute_campaign requires at least 2 products."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client'):
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            brief = {
                "campaign_id": "test",
                "target_region": "Test",
                "target_audience": "Test",
                "campaign_message": "Test",
                "products": [
                    {"name": "Product 1"}
                ]  # Only 1 product
            }
            
            result = orchestrator.execute_campaign(brief)
            
            assert result['status'] == 'failed'
            assert any('at least 2' in str(error).lower() for error in result['errors'])
    
    def test_execute_campaign_compliance_check(self, mock_config, sample_brief):
        """Test that execute_campaign runs compliance checks."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Mock compliance check to fail
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": false, "reason": "Test failure"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Reduce max attempts for faster test
            orchestrator.compliance_agent.max_fix_attempts = 1
            
            result = orchestrator.execute_campaign(sample_brief)
            
            # Should fail compliance
            assert result['status'] == 'failed'
            assert any('compliance' in str(error).lower() for error in result['errors'])
    
    def test_execute_campaign_log_callback(self, mock_config, sample_brief, log_callback):
        """Test that execute_campaign uses log callback."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client, \
             patch('modules.storage_manager.StorageManager.find_asset') as mock_find_asset:
            
            # Mock compliance to pass
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            # Mock asset not found to skip image generation
            mock_find_asset.return_value = None
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            result = orchestrator.execute_campaign(sample_brief, log_callback=log_callback)
            
            # Should have received log messages
            assert len(log_callback.logs) > 0
    
    def test_execute_campaign_progress_updates(self, mock_config, sample_brief):
        """Test that execute_campaign updates progress."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client, \
             patch('modules.storage_manager.StorageManager.find_asset') as mock_find_asset:
            
            # Mock compliance to pass
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            # Mock asset not found
            mock_find_asset.return_value = None
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            result = orchestrator.execute_campaign(sample_brief)
            
            # Should have progress field
            assert 'progress' in result
    
    def test_execute_campaign_with_locale(self, mock_config, sample_brief):
        """Test executing campaign with locale parameter."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client, \
             patch('modules.storage_manager.StorageManager.find_asset') as mock_find_asset:
            
            # Mock compliance to pass
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            mock_find_asset.return_value = None
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            result = orchestrator.execute_campaign(sample_brief, locale="es_ES")
            
            assert result['locale'] == "es_ES"
    
    def test_execute_campaign_with_ab_variant(self, mock_config, sample_brief):
        """Test executing campaign with A/B variant parameter."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client, \
             patch('modules.storage_manager.StorageManager.find_asset') as mock_find_asset:
            
            # Mock compliance to pass
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            mock_find_asset.return_value = None
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            result = orchestrator.execute_campaign(sample_brief, ab_variant="variant_b")
            
            assert result['ab_variant'] == "variant_b"
    
    def test_execute_campaign_unexpected_error_handling(self, mock_config):
        """Test handling of unexpected errors during execution."""
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Setup basic mocks first to let orchestrator initialize
            mock_image_client.return_value = MagicMock()
            mock_compliance_client.return_value = MagicMock()
            
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Now make compliance check raise unexpected error
            def failing_stream(*args, **kwargs):
                raise Exception("Unexpected error")
            orchestrator.compliance_agent.client.models.generate_content_stream = failing_stream
            
            brief = {
                "campaign_id": "test",
                "target_region": "Test",
                "target_audience": "Test",
                "campaign_message": "Test",
                "products": [
                    {"name": "Product 1"},
                    {"name": "Product 2"}
                ]
            }
            
            result = orchestrator.execute_campaign(brief)
            
            assert result['status'] == 'failed'
            assert len(result['errors']) > 0
    
    def test_locale_fallback_to_language_code(self, orchestrator):
        """Test locale matching falls back to language code."""
        brief = {
            "campaign_message": "Default",
            "locales": [
                {
                    "language": "es",
                    "region": "ES",
                    "message": "Spanish message"
                }
            ]
        }
        
        # Try with just language code
        message = orchestrator._get_campaign_message(brief, locale="es")
        
        # Should match on language code
        assert message == "Spanish message"
    
    def test_ab_variant_fallback_to_default(self, orchestrator):
        """Test A/B variant falls back to default if not found."""
        brief = {
            "campaign_message": "Default message",
            "ab_testing": {
                "enabled": True,
                "variants": [
                    {
                        "name": "variant_a",
                        "message": "Variant A"
                    }
                ]
            }
        }
        
        # Request non-existent variant
        message = orchestrator._get_campaign_message(brief, ab_variant="variant_c")
        
        # Should fall back to default
        assert message == "Default message"

