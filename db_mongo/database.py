from odmantic import AIOEngine, Model, ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

from beanie import init_beanie
from app.api.models.estoque import ProdutoEstoqueMongoBeanie



# client = AsyncIOMotorClient("mongodb://localhost:27017")
# Timeout configurable via MONGODB_TIMEOUT_MS (default 15s) — avoids long blocks when Mongo unreachable
_timeout = getattr(settings, "MONGODB_TIMEOUT_MS", 15000)
client = AsyncIOMotorClient(
    settings.MONGODB_URL,
    serverSelectionTimeoutMS=_timeout,
    connectTimeoutMS=_timeout,
    socketTimeoutMS=max(_timeout * 2, 30000),
)  # ODMantic
# client = AsyncIOMotorClient(settings.MONGODB_URL, authSource="admin")
# client = AsyncIOMotorClient("mongodb://mongodb:27017")
# client = AsyncIOMotorClient("mongodb://root:rootpassword@mongodb:27017")
# client = AsyncIOMotorClient("mongodb://root:rootpassword@localhost:27017")

engine = AIOEngine(client=client, database="kapiva_gestao")
db = client.kapiva_gestao


async def init_db():
    await init_beanie(database=db, document_models=[ProdutoEstoqueMongoBeanie])



