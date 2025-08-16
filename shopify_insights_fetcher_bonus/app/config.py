from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MYSQL_URL: str | None = None
    REQUEST_TIMEOUT: int = 20
    USER_AGENT: str = "ShopifyInsightsFetcher/1.0"
    MAX_PAGES: int = 10
    LOG_LEVEL: str = "INFO"
    SERPAPI_KEY: str | None = None
    class Config:
        env_file = ".env"

settings = Settings()
