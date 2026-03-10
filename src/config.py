"""Configuration management for the application"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class AzureOpenAIConfig:
    """Configuration for Azure OpenAI service"""
    endpoint: str
    api_key: str
    api_version: str
    deployment_name: str
    embedding_deployment: str
    embedding_dimension: int

    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """Create configuration from environment variables"""
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        embedding_dimension = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSION", "1536"))

        # Validate required fields
        if not all([endpoint, api_key, api_version, deployment_name, embedding_deployment]):
            raise ValueError(
                "Missing required Azure OpenAI configuration. "
                "Please check your .env file."
            )

        return cls(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment_name,
            embedding_deployment=embedding_deployment,
            embedding_dimension=embedding_dimension
        )


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL database"""
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables"""
        host = os.getenv("DATABASE_HOST", "localhost")
        port = int(os.getenv("DATABASE_PORT", "5432"))
        database = os.getenv("DATABASE_NAME")
        user = os.getenv("DATABASE_USER")
        password = os.getenv("DATABASE_PASSWORD")

        # Validate required fields
        if not all([database, user, password]):
            raise ValueError(
                "Missing required database configuration. "
                "Please check your .env file."
            )

        return cls(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class AppConfig:
    """Main application configuration"""
    azure_openai: AzureOpenAIConfig
    database: DatabaseConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create application configuration from environment variables"""
        return cls(
            azure_openai=AzureOpenAIConfig.from_env(),
            database=DatabaseConfig.from_env()
        )


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create the global configuration instance"""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment variables"""
    global _config
    load_dotenv(override=True)
    _config = AppConfig.from_env()
    return _config
