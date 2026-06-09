from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # escalation timings (seconds)
    escalation_nurse_delay: int = 300      # 5 min
    escalation_charge_nurse_delay: int = 600  # 10 min
    escalation_physician_delay: int = 900  # 15 min

    # openai
    openai_api_key: str = ""

    # kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # redis
    redis_url: str = "redis://localhost:6379/0"

    database_url: str = "postgresql+asyncpg://healthcare:healthcare@localhost:5432/healthcare"

    class Config:
        env_file = ".env"

settings = Settings()