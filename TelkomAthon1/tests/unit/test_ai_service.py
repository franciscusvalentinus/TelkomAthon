"""Unit tests for AI Service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import RateLimitError, APITimeoutError, APIConnectionError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from src.services.ai_service import AIService, AIServiceError
from src.config import AzureOpenAIConfig


@pytest.fixture
def mock_config():
    """Create a mock Azure OpenAI configuration"""
    return AzureOpenAIConfig(
        endpoint="https://openaitcuc.openai.azure.com/",
        api_key="test-api-key",
        api_version="2024-10-01-preview",
        deployment_name="corpu-text-gpt-4o",
        embedding_deployment="corpu-text-embedding-3-large",
        embedding_dimension=1536
    )


@pytest.fixture
def ai_service(mock_config):
    """Create an AI service instance with mock configuration"""
    return AIService(mock_config)


def create_mock_response(content: str) -> ChatCompletion:
    """Helper to create a mock ChatCompletion response"""
    message = ChatCompletionMessage(role="assistant", content=content)
    choice = Choice(
        finish_reason="stop",
        index=0,
        message=message
    )
    return ChatCompletion(
        id="test-id",
        choices=[choice],
        created=1234567890,
        model="gpt-4o",
        object="chat.completion"
    )


class TestAIServiceInitialization:
    """Test AI service initialization"""

    def test_initialization_with_valid_config(self, mock_config):
        """Test that AI service initializes correctly with valid config"""
        service = AIService(mock_config)
        
        assert service.config == mock_config
        assert service.client is not None

    def test_client_configuration(self, ai_service, mock_config):
        """Test that Azure OpenAI client is configured with correct parameters"""
        client = ai_service.client
        
        assert client.api_key == mock_config.api_key
        assert client._base_url.host == "openaitcuc.openai.azure.com"


class TestRetryLogic:
    """Test retry logic with exponential backoff"""

    @patch('src.services.ai_service.time.sleep')
    def test_retry_on_rate_limit_error(self, mock_sleep, ai_service):
        """Test that service retries on rate limit errors with exponential backoff"""
        mock_response = create_mock_response("Success after retry")
        
        ai_service.client.chat.completions.create = Mock(
            side_effect=[
                RateLimitError("Rate limit exceeded", response=Mock(), body=None),
                RateLimitError("Rate limit exceeded", response=Mock(), body=None),
                mock_response
            ]
        )
        
        result = ai_service._call_api_with_retry("test prompt")
        
        assert result == "Success after retry"
        assert ai_service.client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2
        # Check exponential backoff: 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

    @patch('src.services.ai_service.time.sleep')
    def test_retry_on_timeout_error(self, mock_sleep, ai_service):
        """Test that service retries on timeout errors"""
        mock_response = create_mock_response("Success after timeout")
        
        ai_service.client.chat.completions.create = Mock(
            side_effect=[
                APITimeoutError("Timeout"),
                mock_response
            ]
        )
        
        result = ai_service._call_api_with_retry("test prompt")
        
        assert result == "Success after timeout"
        assert ai_service.client.chat.completions.create.call_count == 2
        assert mock_sleep.call_count == 1

    @patch('src.services.ai_service.time.sleep')
    def test_retry_on_connection_error(self, mock_sleep, ai_service):
        """Test that service retries on connection errors"""
        mock_response = create_mock_response("Success after connection error")
        
        ai_service.client.chat.completions.create = Mock(
            side_effect=[
                APIConnectionError("Connection failed"),
                mock_response
            ]
        )
        
        result = ai_service._call_api_with_retry("test prompt")
        
        assert result == "Success after connection error"
        assert ai_service.client.chat.completions.create.call_count == 2

    @patch('src.services.ai_service.time.sleep')
    def test_max_retries_exceeded_rate_limit(self, mock_sleep, ai_service):
        """Test that service raises error after max retries on rate limit"""
        ai_service.client.chat.completions.create = Mock(
            side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body=None)
        )
        
        with pytest.raises(AIServiceError) as exc_info:
            ai_service._call_api_with_retry("test prompt", max_retries=3)
        
        assert "Layanan AI sedang sibuk" in str(exc_info.value)
        assert ai_service.client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('src.services.ai_service.time.sleep')
    def test_max_retries_exceeded_timeout(self, mock_sleep, ai_service):
        """Test that service raises error after max retries on timeout"""
        ai_service.client.chat.completions.create = Mock(
            side_effect=APITimeoutError("Timeout")
        )
        
        with pytest.raises(AIServiceError) as exc_info:
            ai_service._call_api_with_retry("test prompt", max_retries=3)
        
        assert "Koneksi timeout" in str(exc_info.value)
        assert ai_service.client.chat.completions.create.call_count == 3

    def test_no_retry_on_unexpected_error(self, ai_service):
        """Test that service does not retry on unexpected errors"""
        ai_service.client.chat.completions.create = Mock(
            side_effect=ValueError("Unexpected error")
        )
        
        with pytest.raises(AIServiceError) as exc_info:
            ai_service._call_api_with_retry("test prompt")
        
        assert "Terjadi kesalahan saat memanggil layanan AI" in str(exc_info.value)
        assert ai_service.client.chat.completions.create.call_count == 1


class TestOrganizationSummary:
    """Test organization profile summarization"""

    def test_summarize_organization_profile(self, ai_service):
        """Test that organization profile is summarized correctly"""
        org_text = "PT Example adalah perusahaan teknologi yang fokus pada inovasi digital."
        expected_summary = "Ringkasan: PT Example adalah perusahaan teknologi inovatif."
        
        mock_response = create_mock_response(expected_summary)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.summarize_organization_profile(org_text)
        
        assert result == expected_summary
        ai_service.client.chat.completions.create.assert_called_once()
        
        # Verify the prompt contains the organization text
        call_args = ai_service.client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert org_text in messages[0]['content']

    def test_summarize_with_empty_response(self, ai_service):
        """Test handling of empty response from API"""
        mock_response = create_mock_response("")
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.summarize_organization_profile("Some text")
        
        assert result == ""


class TestTLOGeneration:
    """Test Terminal Learning Objectives generation"""

    def test_generate_tlos_returns_correct_count(self, ai_service):
        """Test that TLO generation returns requested number of TLOs"""
        org_context = "Perusahaan teknologi pendidikan"
        course_type = "B2B"
        
        mock_response_text = """1. Peserta mampu menganalisis kebutuhan bisnis klien
2. Peserta mampu merancang solusi teknologi yang tepat
3. Peserta mampu mengimplementasikan sistem B2B
4. Peserta mampu mengevaluasi efektivitas solusi
5. Peserta mampu mengoptimalkan proses bisnis"""
        
        mock_response = create_mock_response(mock_response_text)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.generate_tlos(org_context, course_type, count=5)
        
        assert len(result) == 5
        assert all(isinstance(tlo, str) for tlo in result)
        assert all(len(tlo) > 0 for tlo in result)

    def test_generate_tlos_parses_numbered_list(self, ai_service):
        """Test that TLO generation correctly parses numbered lists"""
        mock_response_text = """1. First TLO
2. Second TLO
3. Third TLO"""
        
        mock_response = create_mock_response(mock_response_text)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.generate_tlos("context", "type", count=3)
        
        assert result == ["First TLO", "Second TLO", "Third TLO"]

    def test_generate_tlos_parses_bulleted_list(self, ai_service):
        """Test that TLO generation correctly parses bulleted lists"""
        mock_response_text = """- First TLO
- Second TLO
- Third TLO"""
        
        mock_response = create_mock_response(mock_response_text)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.generate_tlos("context", "type", count=3)
        
        assert result == ["First TLO", "Second TLO", "Third TLO"]

    def test_generate_tlos_limits_to_requested_count(self, ai_service):
        """Test that TLO generation doesn't return more than requested"""
        mock_response_text = """1. TLO 1
2. TLO 2
3. TLO 3
4. TLO 4
5. TLO 5
6. TLO 6
7. TLO 7"""
        
        mock_response = create_mock_response(mock_response_text)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.generate_tlos("context", "type", count=3)
        
        assert len(result) == 3


class TestPerformanceGeneration:
    """Test performance objectives generation"""

    def test_generate_performances(self, ai_service):
        """Test that performance objectives are generated correctly"""
        tlo_texts = [
            "Peserta mampu menganalisis kebutuhan bisnis",
            "Peserta mampu merancang solusi"
        ]
        
        mock_response_text = """1. Mengidentifikasi stakeholder utama
2. Melakukan analisis SWOT
3. Membuat dokumen requirements
4. Merancang arsitektur sistem
5. Membuat prototype solusi"""
        
        mock_response = create_mock_response(mock_response_text)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.generate_performances(tlo_texts, count=5)
        
        assert len(result) == 5
        assert all(isinstance(perf, str) for perf in result)

    def test_generate_performances_includes_tlo_context(self, ai_service):
        """Test that performance generation includes TLO context in prompt"""
        tlo_texts = ["TLO 1", "TLO 2"]
        
        mock_response = create_mock_response("1. Performance 1\n2. Performance 2")
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        ai_service.generate_performances(tlo_texts, count=2)
        
        call_args = ai_service.client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        prompt = messages[0]['content']
        
        assert "TLO 1" in prompt
        assert "TLO 2" in prompt


class TestELOGeneration:
    """Test Enabling Learning Objectives generation"""

    def test_generate_elos(self, ai_service):
        """Test that ELOs are generated correctly"""
        performance_texts = [
            "Mengidentifikasi stakeholder utama",
            "Melakukan analisis SWOT"
        ]
        
        mock_response_text = """1. Membuat daftar stakeholder
2. Mengklasifikasikan stakeholder berdasarkan pengaruh
3. Menyusun matriks SWOT
4. Menganalisis faktor internal
5. Menganalisis faktor eksternal
6. Membuat strategi berdasarkan SWOT"""
        
        mock_response = create_mock_response(mock_response_text)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.generate_elos(performance_texts, count=3)
        
        assert len(result) >= 3
        assert all(isinstance(elo, str) for elo in result)

    def test_generate_elos_includes_performance_context(self, ai_service):
        """Test that ELO generation includes performance context in prompt"""
        performance_texts = ["Performance 1", "Performance 2"]
        
        mock_response = create_mock_response("1. ELO 1\n2. ELO 2\n3. ELO 3")
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        ai_service.generate_elos(performance_texts, count=3)
        
        call_args = ai_service.client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        prompt = messages[0]['content']
        
        assert "Performance 1" in prompt
        assert "Performance 2" in prompt


class TestSyllabusFormatting:
    """Test syllabus content formatting"""

    def test_format_syllabus_content(self, ai_service):
        """Test that syllabus content is formatted correctly"""
        org_summary = "PT Example - Perusahaan teknologi"
        tlos = ["TLO 1", "TLO 2"]
        performances = ["Performance 1", "Performance 2"]
        elos = ["ELO 1", "ELO 2", "ELO 3"]
        
        expected_content = "# SILABUS KURSUS\n\n## Profil Organisasi\nPT Example..."
        mock_response = create_mock_response(expected_content)
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = ai_service.format_syllabus_content(
            org_summary, tlos, performances, elos
        )
        
        assert result == expected_content

    def test_format_syllabus_includes_all_components(self, ai_service):
        """Test that syllabus formatting includes all components in prompt"""
        org_summary = "Organization summary"
        tlos = ["TLO 1"]
        performances = ["Performance 1"]
        elos = ["ELO 1"]
        
        mock_response = create_mock_response("Formatted syllabus")
        ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        ai_service.format_syllabus_content(org_summary, tlos, performances, elos)
        
        call_args = ai_service.client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        prompt = messages[0]['content']
        
        assert org_summary in prompt
        assert "TLO 1" in prompt
        assert "Performance 1" in prompt
        assert "ELO 1" in prompt
