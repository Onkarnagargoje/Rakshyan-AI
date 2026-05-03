from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "SafeNest AI"
    env: str = "dev"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 240

    database_url: str = "postgresql+psycopg://safenest:safenest@localhost:5432/safenest"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    enable_ollama: bool = True

    enable_transformers: bool = True

    log_level: str = "INFO"
    log_hash_chain_salt: str = "dev-only-salt"

    cors_origins: str = "http://localhost:3000"


settings = Settings()

