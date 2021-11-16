from odmantic import AIOEngine, Model, ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


# client = AsyncIOMotorClient("mongodb://localhost:27017")
client = AsyncIOMotorClient(settings.MONGODB_URL)
# client = AsyncIOMotorClient(settings.MONGODB_URL, authSource="admin")
# client = AsyncIOMotorClient("mongodb://mongodb:27017")
# client = AsyncIOMotorClient("mongodb://root:rootpassword@mongodb:27017")
# client = AsyncIOMotorClient("mongodb://root:rootpassword@localhost:27017")


engine = AIOEngine(motor_client=client, database="kapiva_gestao")

