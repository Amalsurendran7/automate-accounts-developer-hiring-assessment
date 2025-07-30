from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    """
    This class defines the settings for the app
    """

    
    SQL_CONNECTION: str
    

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
