from odmantic import AIOEngine, Model, ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

from beanie import init_beanie
from api.models.estoque import ProdutoEstoqueMongoBeanie



# client = AsyncIOMotorClient("mongodb://localhost:27017")
client = AsyncIOMotorClient(settings.MONGODB_URL)       # ODMantic
# client = AsyncIOMotorClient(settings.MONGODB_URL, authSource="admin")
# client = AsyncIOMotorClient("mongodb://mongodb:27017")
# client = AsyncIOMotorClient("mongodb://root:rootpassword@mongodb:27017")
# client = AsyncIOMotorClient("mongodb://root:rootpassword@localhost:27017")

engine = AIOEngine(client=client, database="kapiva_gestao")
db = client.kapiva_gestao


async def init_db():
    await init_beanie(database=db, document_models=[ProdutoEstoqueMongoBeanie])



