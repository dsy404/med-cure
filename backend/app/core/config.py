import os
from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MedWise"
    TAGLINE: str = "Every medicine match. Every price. Every claim backed by evidence."
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    EVIDENCE_DB_PATH: Path = BASE_DIR / "backend" / "medledger_evidence.db"
    
    # Dataset files
    GENERIC_PRODUCTS_CSV: Path = DATA_DIR / "generic_products_clean.csv"
    CEILING_PRICES_CSV: Path = DATA_DIR / "ceiling_prices_clean.csv"
    DATA_QUALITY_REPORT: Path = DATA_DIR / "data_quality_report.txt"
    RS_SESSION_CSV: Path = DATA_DIR / "RS_Session_255_AU_1784_B.csv"
    
    # AI settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    GEMMA_MODEL_NAME: str = os.getenv("GEMMA_MODEL_NAME", "gemma2:2b")
    OLLAMA_TIMEOUT_SECONDS: float = 8.0
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    model_config = ConfigDict(case_sensitive=True)

settings = Settings()
