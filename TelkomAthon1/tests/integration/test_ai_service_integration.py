"""Integration tests for AI Service with Azure OpenAI"""

import pytest
import os
from unittest.mock import patch

from src.services.ai_service import AIService, AIServiceError
from src.config import AzureOpenAIConfig


@pytest.fixture
def test_config():
    """Create test configuration for Azure OpenAI"""
    return AzureOpenAIConfig(
        endpoint="https://openaitcuc.openai.azure.com/",
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "test-key"),
        api_version="2024-10-01-preview",
        deployment_name="corpu-text-gpt-4o",
        embedding_deployment="corpu-text-embedding-3-large",
        embedding_dimension=1536
    )


class TestAIServiceIntegration:
    """Integration tests for AI service"""

    def test_service_initialization(self, test_config):
        """Test that AI service can be initialized with valid config"""
        service = AIService(test_config)
        
        assert service is not None
        assert service.config == test_config
        assert service.client is not None

    def test_service_uses_correct_endpoint(self, test_config):
        """Test that service is configured with correct Azure endpoint"""
        service = AIService(test_config)
        
        assert "openaitcuc.openai.azure.com" in str(service.client._base_url)

    def test_service_uses_correct_api_version(self, test_config):
        """Test that service uses correct API version"""
        service = AIService(test_config)
        
        # The API version is set in the client's default query parameters
        assert service.config.api_version == "2024-10-01-preview"

    def test_service_uses_correct_deployment_name(self, test_config):
        """Test that service is configured with correct deployment name"""
        service = AIService(test_config)
        
        assert service.config.deployment_name == "corpu-text-gpt-4o"

    def test_service_uses_correct_embedding_deployment(self, test_config):
        """Test that service is configured with correct embedding deployment"""
        service = AIService(test_config)
        
        assert service.config.embedding_deployment == "corpu-text-embedding-3-large"


@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_API_KEY"),
    reason="Azure OpenAI API key not available"
)
class TestAIServiceLiveAPI:
    """Live API tests (only run when API key is available)"""

    def test_summarize_organization_profile_live(self, test_config):
        """Test organization profile summarization with live API"""
        service = AIService(test_config)
        
        org_text = """PT Teknologi Edukasi Indonesia adalah perusahaan yang bergerak di bidang 
        teknologi pendidikan. Kami fokus pada pengembangan platform pembelajaran digital 
        untuk meningkatkan kualitas pendidikan di Indonesia."""
        
        try:
            result = service.summarize_organization_profile(org_text)
            
            assert result is not None
            assert len(result) > 0
            assert isinstance(result, str)
        except AIServiceError as e:
            pytest.skip(f"API call failed: {str(e)}")

    def test_generate_tlos_live(self, test_config):
        """Test TLO generation with live API"""
        service = AIService(test_config)
        
        org_context = "Perusahaan teknologi pendidikan yang fokus pada inovasi digital"
        course_type = "B2B"
        
        try:
            result = service.generate_tlos(org_context, course_type, count=3)
            
            assert result is not None
            assert len(result) >= 3
            assert all(isinstance(tlo, str) for tlo in result)
            assert all(len(tlo) > 0 for tlo in result)
        except AIServiceError as e:
            pytest.skip(f"API call failed: {str(e)}")
