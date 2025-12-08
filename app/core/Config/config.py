from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    MONGO_PASS: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    R2_TOKEN_VALUE: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_S3: str
    R2_BUCKET: str
    VERSION: str = "1.0.0"
    APP_MODE: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False,        
        extra="ignore"  
    )
settings = Settings()