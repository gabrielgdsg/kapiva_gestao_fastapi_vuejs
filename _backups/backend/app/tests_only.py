from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from odmantic import Model, EmbeddedModel

fake_db = {}


class Item(Model):
    title: str
    timestamp: datetime
    description: Optional[str] = None


app = FastAPI()


@app.put("/items/{id}")
def update_item(id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    fake_db[id] = json_compatible_item_data


if __name__ == "__main__":
    import asyncio
    import uvicorn
    loop = asyncio.get_event_loop()
    config = uvicorn.Config(app=app, port=80, loop=loop, host="0.0.0.0")
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())