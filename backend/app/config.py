import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ENV: Literal["development", "production", "testing"] = os.getenv("NETRA_ENV", "development")
    DEBUG: bool = ENV == "development"

    API_TITLE = "NETRA API"
    API_VERSION = "0.1.0"

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    DATABASE_URL = os.getenv("DATABASE_URL", None)
    NEO4J_URI = os.getenv("NEO4J_URI", None)
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    INTEGRATION_MODE = os.getenv("INTEGRATION_MODE", "synthetic")

    @property
    def database_configured(self) -> bool:
        return bool(self.DATABASE_URL)

    @property
    def neo4j_configured(self) -> bool:
        return bool(self.NEO4J_URI)

settings = Settings()
