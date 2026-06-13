"""
Configuration Management Module

This module handles all application configuration using Pydantic Settings.
Pydantic provides automatic type validation and environment variable loading.

Why use Pydantic Settings?
- Type safety: Ensures configuration values are the correct type
- Environment variables: Automatically loads from .env file
- Validation: Raises errors if required values are missing or invalid
- IDE support: Auto-completion and type hints

For beginners: This is a centralized place to manage all settings
instead of hardcoding values throughout the application.
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings class that inherits from Pydantic BaseSettings.
    
    This class automatically reads environment variables and provides
    type validation. The field names should match environment variable names
    (in uppercase) or can be customized with aliases.
    
    Attributes:
        escalation_nurse_delay: Seconds before escalating to nurse (default: 300 = 5 minutes)
        escalation_charge_nurse_delay: Seconds before escalating to charge nurse (default: 600 = 10 minutes)
        escalation_physician_delay: Seconds before escalating to physician (default: 900 = 15 minutes)
        openai_api_key: API key for OpenAI GPT-4o service
        kafka_bootstrap_servers: Kafka server address for event streaming
        redis_url: Redis server URL for caching and task queue
        database_url: PostgreSQL database connection string
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log output format (json for production, console for development)
    """
    
    # Escalation timings (in seconds)
    # These control how long to wait before escalating unacknowledged alerts
    escalation_nurse_delay: int = 300      # 5 minutes
    escalation_charge_nurse_delay: int = 600  # 10 minutes
    escalation_physician_delay: int = 900  # 15 minutes

    # OpenAI API configuration
    # Used for LLM-powered alert summarization
    openai_api_key: str = ""

    # Kafka configuration
    # Kafka is a distributed event streaming platform
    kafka_bootstrap_servers: str = "localhost:9092"

    # Redis configuration
    # Redis is used for caching and as a message broker for Celery
    redis_url: str = "redis://localhost:6379/0"

    # Database configuration
    # PostgreSQL connection URL with asyncpg driver for async operations
    database_url: str = "postgresql+asyncpg://healthcare:healthcare@localhost:5432/healthcare"

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json for production, console for development

    class Config:
        """
        Pydantic configuration class.
        
        This tells Pydantic to load environment variables from a .env file.
        The .env file should never be committed to version control as it
        contains sensitive information like API keys.
        """
        env_file = ".env"

# Create a global settings instance
# This instance is imported throughout the application to access configuration
settings = Settings()