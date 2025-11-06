"""
Integration tests for complete campaign workflows.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from PIL import Image
import io


@pytest.mark.integration
class TestCampaignWorkflow:
    """Test suite for complete campaign workflows."""
    
    def test_campaign_with_existing_assets(self, mock_config, sample_brief, sample_image, temp_storage):
        """Test campaign workflow with existing assets."""
        with patch('modules.image_generator.genai.Client'), \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Mock compliance to pass
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Create mock assets
            for product in sample_brief['products']:
                asset_folder = temp_storage['assets'] / product['asset_filename']
                asset_folder.mkdir()
                sample_image.save(asset_folder / "image.jpg")
            
            # Execute campaign
            result = orchestrator.execute_campaign(sample_brief)
            
            assert result['status'] == 'completed'
            assert len(result['output_paths']) == len(sample_brief['products'])
    
    def test_campaign_with_generated_images(self, mock_config, sample_brief, sample_image):
        """Test campaign workflow with AI-generated images."""
        # Mock image generation
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Setup image mock - use SimpleNamespace for simple attribute access
            def image_stream(*args, **kwargs):
                from types import SimpleNamespace
                
                # Create simple objects with just the attributes we need
                inline_data = SimpleNamespace(data=image_bytes)
                part = SimpleNamespace(inline_data=inline_data)
                content = SimpleNamespace(parts=[part])
                candidate = SimpleNamespace(content=content)
                chunk = SimpleNamespace(candidates=[candidate])
                
                yield chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Setup compliance mock
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Execute campaign (no assets, will generate)
            result = orchestrator.execute_campaign(sample_brief)
            
            assert result['status'] == 'completed'
            assert len(result['output_paths']) > 0
    
    def test_campaign_with_compliance_auto_fix(self, mock_config, sample_brief_noncompliant, sample_image):
        """Test campaign workflow with compliance auto-fix."""
        # Mock image generation  
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Setup image mock - use SimpleNamespace for simple attribute access
            def image_stream(*args, **kwargs):
                from types import SimpleNamespace
                
                # Create simple objects with just the attributes we need
                inline_data = SimpleNamespace(data=image_bytes)
                part = SimpleNamespace(inline_data=inline_data)
                content = SimpleNamespace(parts=[part])
                candidate = SimpleNamespace(content=content)
                chunk = SimpleNamespace(candidates=[candidate])
                
                yield chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            call_count = [0]
            
            def mock_stream(*args, **kwargs):
                call_count[0] += 1
                
                # First call: fail compliance
                if call_count[0] == 1:
                    mock_chunk = MagicMock()
                    mock_chunk.text = '{"compliant": false, "reason": "Contains forbidden terms"}'
                    yield mock_chunk
                # Second call: return fix
                elif call_count[0] == 2:
                    mock_chunk = MagicMock()
                    mock_chunk.text = '{"fixed_message": "Quality products for sustainability", "explanation": "Removed forbidden terms"}'
                    yield mock_chunk
                # Remaining calls: pass compliance
                else:
                    mock_chunk = MagicMock()
                    mock_chunk.text = '{"compliant": true, "reason": "Now compliant"}'
                    yield mock_chunk
            
            mock_client = MagicMock()
            mock_client.models.generate_content_stream = mock_stream
            mock_compliance_client.return_value = mock_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Execute campaign with non-compliant brief
            result = orchestrator.execute_campaign(sample_brief_noncompliant)
            
            # Should succeed after auto-fix
            assert result['status'] == 'completed'
            assert 'compliance_fixes' in result
    
    def test_campaign_with_spanish_locale(self, mock_config, sample_brief, sample_image):
        """Test campaign workflow with Spanish locale."""
        # Mock image generation
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Setup image mock - use SimpleNamespace for simple attribute access
            def image_stream(*args, **kwargs):
                from types import SimpleNamespace
                
                # Create simple objects with just the attributes we need
                inline_data = SimpleNamespace(data=image_bytes)
                part = SimpleNamespace(inline_data=inline_data)
                content = SimpleNamespace(parts=[part])
                candidate = SimpleNamespace(content=content)
                chunk = SimpleNamespace(candidates=[candidate])
                
                yield chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Setup compliance mock
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Execute campaign with Spanish locale
            result = orchestrator.execute_campaign(sample_brief, locale="es_ES")
            
            assert result['status'] == 'completed'
            assert result['locale'] == "es_ES"
    
    def test_campaign_with_ab_variant(self, mock_config, sample_brief, sample_image):
        """Test campaign workflow with A/B variant."""
        # Mock image generation
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Setup image mock - use SimpleNamespace for simple attribute access
            def image_stream(*args, **kwargs):
                from types import SimpleNamespace
                
                # Create simple objects with just the attributes we need
                inline_data = SimpleNamespace(data=image_bytes)
                part = SimpleNamespace(inline_data=inline_data)
                content = SimpleNamespace(parts=[part])
                candidate = SimpleNamespace(content=content)
                chunk = SimpleNamespace(candidates=[candidate])
                
                yield chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Setup compliance mock
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Execute campaign with A/B variant
            result = orchestrator.execute_campaign(sample_brief, ab_variant="variant_b")
            
            assert result['status'] == 'completed'
            assert result['ab_variant'] == "variant_b"
    
    def test_campaign_with_multiple_products(self, mock_config, sample_image):
        """Test campaign workflow with multiple products."""
        # Mock image generation
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        with patch('modules.image_generator.genai.Client') as mock_image_client, \
             patch('modules.compliance_agent.genai.Client') as mock_compliance_client:
            
            # Setup image mock - use SimpleNamespace for simple attribute access
            def image_stream(*args, **kwargs):
                from types import SimpleNamespace
                
                # Create simple objects with just the attributes we need
                inline_data = SimpleNamespace(data=image_bytes)
                part = SimpleNamespace(inline_data=inline_data)
                content = SimpleNamespace(parts=[part])
                candidate = SimpleNamespace(content=content)
                chunk = SimpleNamespace(candidates=[candidate])
                
                yield chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            # Setup compliance mock
            compliance_chunk = MagicMock()
            compliance_chunk.text = '{"compliant": true, "reason": "Passed"}'
            
            def compliance_stream(*args, **kwargs):
                yield compliance_chunk
            
            compliance_client = MagicMock()
            compliance_client.models.generate_content_stream = compliance_stream
            mock_compliance_client.return_value = compliance_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            # Brief with 3 products
            brief = {
                "campaign_id": "multi-product-test",
                "target_region": "Global",
                "target_audience": "Test audience",
                "campaign_message": "Quality products",
                "products": [
                    {"name": "Product 1", "description": "First product", "asset_filename": "product1"},
                    {"name": "Product 2", "description": "Second product", "asset_filename": "product2"},
                    {"name": "Product 3", "description": "Third product", "asset_filename": "product3"}
                ]
            }
            
            result = orchestrator.execute_campaign(brief)
            
            assert result['status'] == 'completed'
            assert len(result['output_paths']) == 3
            
            # Each product should have 3 creatives (3 aspect ratios)
            for product_name, product_data in result['output_paths'].items():
                assert len(product_data['creatives']) == 3
    
    def test_campaign_error_handling(self, mock_config, sample_brief):
        """Test campaign workflow handles errors gracefully."""
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
            
            # Mock image generation to fail
            def image_stream(*args, **kwargs):
                raise Exception("Image generation failed")
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            result = orchestrator.execute_campaign(sample_brief)
            
            # Should handle error gracefully
            assert 'status' in result
            assert len(result['errors']) > 0
    
    def test_campaign_progress_tracking(self, mock_config, sample_brief, sample_image):
        """Test that campaign tracks progress through workflow."""
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
            
            def image_stream(*args, **kwargs):
                image_chunk = MagicMock()
                image_chunk.candidates = [MagicMock()]
                image_chunk.candidates[0].content = MagicMock()
                image_chunk.candidates[0].content.parts = [MagicMock()]
                mock_inline_data = MagicMock()
                mock_inline_data.data = image_bytes
                image_chunk.candidates[0].content.parts[0].inline_data = mock_inline_data
                yield image_chunk
            
            image_client = MagicMock()
            image_client.models.generate_content_stream = image_stream
            mock_image_client.return_value = image_client
            
            from modules.orchestrator import CampaignOrchestrator
            orchestrator = CampaignOrchestrator(mock_config)
            
            result = orchestrator.execute_campaign(sample_brief)
            
            # Should have progress tracking
            assert 'progress' in result
            if result['status'] == 'completed':
                assert result['progress'] == 100

