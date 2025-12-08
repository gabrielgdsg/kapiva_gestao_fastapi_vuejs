from beanie import Document
from pydantic.schema import Optional
from datetime import datetime


class Configs(Document):
    dat_last_movto_from_postgres_update: Optional[datetime]

    class Settings:
        name = "settings"