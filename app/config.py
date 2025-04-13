from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

# class Cfg(BaseSettings):
#     env_file:ClassVar[Path] = BASE_DIR / ".env"

load_dotenv()

class DatabaseSettings(BaseSettings):
    db_postgres_host: str = '0.0.0.0'
    db_postgres_port: str = '5432'
    db_postgres_name: str
    db_postgres_username: str
    db_postgres_password: str
    db_postgres_timeout: int = 5
    db_postgres_driver: Literal["psycopg", "psycopg2"] = "psycopg"

    @property
    def postgres_host_url(self):
        return (
            f"postgresql+{self.db_postgres_driver}://"
            f"{self.db_postgres_username}:{self.db_postgres_password}"
            f"@{self.db_postgres_host}:{self.db_postgres_port}/"
        )

    @property
    def postgres_database_url(self):
        return f"{self.postgres_host_url}{self.db_postgres_name}"

class RabbitSettings(BaseSettings):
    mq_user:str
    mq_pass:str
    mq_port:str  
    mq_host:str

    @property
    def rabbit_url(self):
        return f'amqp://{self.mq_user}:{self.mq_pass}@{self.mq_host}:{self.mq_port}//'

class ExtraSettings(BaseSettings): ...

class EmailSettings(BaseSettings):
    email_pass:str | None = None
    email_login:str | None = None

class AuthSettings(BaseSettings):
    secret_key: str 
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int

class Settings(DatabaseSettings, ExtraSettings, AuthSettings, RabbitSettings, EmailSettings):
    app_title: str = "CRM"
    app_description: str = ""
    mock_external_services: bool = False
    local: bool = False


app_settings = Settings()

