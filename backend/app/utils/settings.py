from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "SafeNest AI"
    env: str = "dev"
    # Set in deploy (e.g. git SHA) to confirm running code: GET /health, OpenAPI info.version, startup log
    app_build_id: str = ""

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 240

    database_url: str = "postgresql+asyncpg://safenest:safenest@localhost:5432/safenest"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    enable_ollama: bool = True
    # Seconds; multilingual prompts can be slower on CPU
    ollama_timeout_sec: int = 90

    enable_transformers: bool = True

    # Optional Google Gemini (Developer API key — paid; improves borderline cases)
    enable_gemini: bool = False
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    log_level: str = "INFO"
    log_hash_chain_salt: str = "dev-only-salt"

    cors_origins: str = "http://localhost:3000"

    # Push notifications (FCM HTTP v1)
    enable_push: bool = False
    fcm_project_id: str = ""
    # Provide either a filesystem path to a service account JSON, or the JSON itself.
    fcm_service_account_path: str = ""
    fcm_service_account_json: str = ""


settings = Settings()

