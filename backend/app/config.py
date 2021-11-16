from pydantic import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    MONGODB_URL: str
    UVICORN_HOST: str

    class Config:
        env_file = '../../develop_pycharm.env'
        # env_file = '../../develop_docker.env'
        # env_file = '../../prod.env'


settings = Settings()
