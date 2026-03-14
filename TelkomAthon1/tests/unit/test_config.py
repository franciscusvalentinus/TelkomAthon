"""Unit tests for configuration management"""

import pytest
import os
from src.config import AzureOpenAIConfig, DatabaseConfig, AppConfig


class TestAzureOpenAIConfig:
    """Tests for Azure OpenAI configuration"""
    
    def test_from_env_with_valid_config(self, monkeypatch):
        """Test creating config from valid environment variables"""
        # Arrange
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "test-deployment")
        monkeypatch.setenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "test-embedding")
        monkeypatch.setenv("AZURE_OPENAI_EMBEDDING_DIMENSION", "1536")
        
        # Act
        config = AzureOpenAIConfig.from_env()
        
        # Assert
        assert config.endpoint == "https://test.openai.azure.com/"
        assert config.api_key == "test-key"
        assert config.api_version == "2024-10-01-preview"
        assert config.deployment_name == "test-deployment"
        assert config.embedding_deployment == "test-embedding"
        assert config.embedding_dimension == 1536
    
    def test_from_env_with_missing_config(self, monkeypatch):
        """Test that missing config raises ValueError"""
        # Arrange - clear all env vars
        for key in ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", 
                    "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_DEPLOYMENT_NAME",
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]:
            monkeypatch.delenv(key, raising=False)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required Azure OpenAI configuration"):
            AzureOpenAIConfig.from_env()


class TestDatabaseConfig:
    """Tests for database configuration"""
    
    def test_from_env_with_valid_config(self, monkeypatch):
        """Test creating config from valid environment variables"""
        # Arrange
        monkeypatch.setenv("DATABASE_HOST", "localhost")
        monkeypatch.setenv("DATABASE_PORT", "5432")
        monkeypatch.setenv("DATABASE_NAME", "test_db")
        monkeypatch.setenv("DATABASE_USER", "test_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "test_pass")
        
        # Act
        config = DatabaseConfig.from_env()
        
        # Assert
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.user == "test_user"
        assert config.password == "test_pass"
    
    def test_get_connection_string(self, monkeypatch):
        """Test connection string generation"""
        # Arrange
        monkeypatch.setenv("DATABASE_HOST", "localhost")
        monkeypatch.setenv("DATABASE_PORT", "5432")
        monkeypatch.setenv("DATABASE_NAME", "test_db")
        monkeypatch.setenv("DATABASE_USER", "test_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "test_pass")
        
        config = DatabaseConfig.from_env()
        
        # Act
        conn_string = config.get_connection_string()
        
        # Assert
        assert conn_string == "postgresql://test_user:test_pass@localhost:5432/test_db"
    
    def test_from_env_with_missing_config(self, monkeypatch):
        """Test that missing config raises ValueError"""
        # Arrange - clear required env vars
        for key in ["DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD"]:
            monkeypatch.delenv(key, raising=False)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required database configuration"):
            DatabaseConfig.from_env()
