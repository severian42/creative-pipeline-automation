"""
Unit tests for ComplianceAgent.
"""

import pytest
from unittest.mock import MagicMock, patch
from modules.compliance_agent import ComplianceAgent


@pytest.mark.unit
class TestComplianceAgent:
    """Test suite for ComplianceAgent."""
    
    def test_initialization(self, mock_config):
        """Test ComplianceAgent initializes correctly."""
        with patch('modules.compliance_agent.genai.Client') as mock_client:
            agent = ComplianceAgent(mock_config)
            
            assert agent.config == mock_config
            assert agent.model == "gemini-flash-latest"
            assert agent.brand_guidelines is not None
            assert agent.max_fix_attempts == 5
    
    def test_legal_compliance_pass(self, mock_config):
        """Test legal compliance check passes for valid message."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock successful compliance response
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Message is appropriate and compliant"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            is_compliant, reason = agent.check_legal_compliance(
                "Quality products built to last"
            )
            
            assert is_compliant is True
            assert "appropriate" in reason.lower() or "compliant" in reason.lower()
    
    def test_legal_compliance_fail(self, mock_config):
        """Test legal compliance check fails for discriminatory content."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock failed compliance response
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": false, "reason": "Contains discriminatory language"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            is_compliant, reason = agent.check_legal_compliance(
                "Men only - whites preferred"
            )
            
            assert is_compliant is False
            assert "discriminatory" in reason.lower()
    
    def test_brand_compliance_pass(self, mock_config):
        """Test brand compliance check passes for aligned message."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock successful compliance response
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Aligns with Patagonia values"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            is_compliant, reason = agent.check_brand_compliance(
                "Built to endure. Designed to be repaired.",
                "Eco-conscious consumers"
            )
            
            assert is_compliant is True
    
    def test_brand_compliance_fail_forbidden_terms(self, mock_config):
        """Test brand compliance fails for forbidden terms."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock failed compliance response
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": false, "reason": "Contains forbidden terms like \'buy now\' and \'guaranteed\'"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            is_compliant, reason = agent.check_brand_compliance(
                "BUY NOW! Guaranteed results!",
                "General consumers"
            )
            
            assert is_compliant is False
            assert "forbidden" in reason.lower() or "buy now" in reason.lower()
    
    def test_compliance_with_locale(self, mock_config):
        """Test compliance check with locale parameter."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Spanish message is compliant"}'
            
            def mock_stream(*args, **kwargs):
                # Verify locale is mentioned in the prompt
                prompt = args[0] if args else kwargs.get('contents', [{}])[0].parts[0].text
                assert 'Spanish' in prompt or 'es_ES' in str(kwargs)
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            is_compliant, reason = agent.check_legal_compliance(
                "Productos de calidad",
                locale="es_ES"
            )
            
            assert is_compliant is True
    
    def test_fix_compliance_issues(self, mock_config):
        """Test automatic compliance issue fixing."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock fix response
            mock_chunk = MagicMock()
            mock_chunk.text = '{"fixed_message": "Quality products for a sustainable future", "explanation": "Removed forbidden terms"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            success, fixed_msg, explanation = agent.fix_compliance_issues(
                "BUY NOW! Guaranteed!",
                "General consumers",
                "Contains forbidden terms"
            )
            
            assert success is True
            assert fixed_msg == "Quality products for a sustainable future"
            assert "forbidden" in explanation.lower()
    
    def test_fix_compliance_empty_response(self, mock_config):
        """Test fix handling when LLM returns empty message."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock empty fix response
            mock_chunk = MagicMock()
            mock_chunk.text = '{"fixed_message": "", "explanation": "Could not fix"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            success, fixed_msg, explanation = agent.fix_compliance_issues(
                "Bad message",
                "Audience",
                "Issue"
            )
            
            assert success is False
            assert fixed_msg == "Bad message"  # Original message returned
    
    def test_validate_campaign_pass(self, mock_config, sample_brief):
        """Test complete campaign validation that passes."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock all compliance checks pass
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "All checks passed"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            is_compliant, reason, fixed_data = agent.validate_campaign(
                sample_brief,
                auto_fix=True
            )
            
            assert is_compliant is True
            assert fixed_data is None  # No fixes needed
    
    def test_validate_campaign_with_auto_fix(self, mock_config):
        """Test campaign validation with successful auto-fix."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
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
                # Third and fourth calls: pass compliance
                else:
                    mock_chunk = MagicMock()
                    mock_chunk.text = '{"compliant": true, "reason": "Now compliant"}'
                    yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            brief = {
                "campaign_message": "BUY NOW! Guaranteed!",
                "target_audience": "General"
            }
            
            is_compliant, reason, fixed_data = agent.validate_campaign(
                brief,
                auto_fix=True
            )
            
            assert is_compliant is True
            assert fixed_data is not None
            assert fixed_data["campaign_message"] == "Quality products for sustainability"
    
    def test_validate_campaign_max_attempts_exhausted(self, mock_config):
        """Test campaign validation fails after max attempts."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Always fail compliance
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": false, "reason": "Still not compliant"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            agent.max_fix_attempts = 2  # Reduce for faster test
            
            brief = {
                "campaign_message": "Bad message",
                "target_audience": "General"
            }
            
            is_compliant, reason, fixed_data = agent.validate_campaign(
                brief,
                auto_fix=True
            )
            
            assert is_compliant is False
            assert "after" in reason.lower() and "attempts" in reason.lower()
    
    def test_json_parsing_error_handling(self, mock_config):
        """Test handling of malformed JSON responses."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            # Mock malformed JSON response
            mock_chunk = MagicMock()
            mock_chunk.text = 'This is not JSON at all'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            # Should default to pass with warning
            is_compliant, reason = agent.check_legal_compliance(
                "Test message"
            )
            
            assert is_compliant is True
            assert "completed" in reason.lower()
    
    def test_api_exception_handling(self, mock_config):
        """Test handling of API exceptions."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            def mock_stream(*args, **kwargs):
                raise Exception("API Error")
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            # Should default to pass with warning
            is_compliant, reason = agent.check_legal_compliance(
                "Test message"
            )
            
            assert is_compliant is True
            assert "warning" in reason.lower() or "error" in reason.lower()
    
    def test_log_callback(self, mock_config, log_callback):
        """Test that log callback receives messages."""
        with patch('modules.compliance_agent.genai.Client') as mock_client_class:
            mock_client = MagicMock()
            
            mock_chunk = MagicMock()
            mock_chunk.text = '{"compliant": true, "reason": "Test"}'
            
            def mock_stream(*args, **kwargs):
                yield mock_chunk
            
            mock_client.models.generate_content_stream = mock_stream
            mock_client_class.return_value = mock_client
            
            agent = ComplianceAgent(mock_config)
            
            agent.check_legal_compliance(
                "Test message",
                log_callback=log_callback
            )
            
            assert len(log_callback.logs) > 0
            assert any("compliance" in log.lower() for log in log_callback.logs)

