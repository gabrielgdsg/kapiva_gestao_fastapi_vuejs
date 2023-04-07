from typing import List
from fastapi_offline import FastAPIOffline
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from api.comissao import api_comissao
from api.financeiro import api_caixa
from api.levantamentos import api_levantamentos
from api.estoque import api_estoque
from db_postgres.connection import PostgresDatabase
from config import settings
# from api.models import User
from db_mongo.database import engine, ObjectId

app = FastAPIOffline()
# app = FastAPI()

app.include_router(api_levantamentos.router)
app.include_router(api_estoque.router)
app.include_router(api_comissao.router)
app.include_router(api_caixa.router)


PostgresDatabase.initialise(user=settings.POSTGRES_USER, password=settings.POSTGRES_PASSWORD, database=settings.POSTGRES_DATABASE, host=settings.POSTGRES_HOST, port=settings.POSTGRES_PORT)
# PostgresDatabase.initialise(user='postgres', password=36217900, database='LOGTEC', host='CAIXA',  port='5432')  # ip:192.168.1.151
# PostgresDatabase.initialise(user='postgres', password=36217900, database='LOGTEC', host='192.168.1.151',  port='5432')  # ip:192.168.1.151
## PostgresDatabase.initialise(user='postgres', password=36217900, database='LOGTEC', host='postgresqlhost',  port='5432')# ip:192.168.1.151
# PostgresDatabase.initialise(user='postgres', password=36217900, database='logtec_test', host='host.docker.internal', port='5432') #when using docker host='host.docker.internal'
# PostgresDatabase.initialise(user='postgres', password=36217900, database='logtec_test', host='localhost', port='5432') #when not using docker host='localhost'


origins = [
    '*'
    # 'http://127.0.0.1:8080',
    # 'http://192.168.1.201:8080',
    # 'http://localhost:80',
    # 'http://localhost:8080',
    # 'http://127.0.0.1:80'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run('main:app', port=80, host=settings.UVICORN_HOST, log_level="info", reload=True, debug=True)
#     # uvicorn.run(app=app, host="0.0.0.0", port=80, debug=True)


if __name__ == "__main__":
    import asyncio
    import uvicorn
    loop = asyncio.get_event_loop()
    config = uvicorn.Config(app=app, port=80, loop=loop, host=settings.UVICORN_HOST, log_level="info", reload=True)
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())
#
#     from uvicorn.reloaders.statreload import StatReload
#     from uvicorn.main import run, get_logger
#
#     reloader = StatReload(get_logger(run_config['log_level']))
#     reloader.run(run, {
#         'app': app,
#         'host': run_config['api_host'],
#         'port': run_config['api_port'],
#         'log_level': run_config['log_level'],
#         'debug': 'true'
#     })


# @app.put("/api/users/", response_model=User)
# async def create_user(user: User):
#     await engine.save(user)
#     return user
#
#
# @app.get("/api/users", response_model=List[User])
# async def get_users():
#     users = await engine.find(User)
#     return users
#
#
# @app.get("/api/users/{id}", response_model=User)
# async def get_user_by_id(id: ObjectId):
#     user = await engine.find_one(User, User.id == id)
#     if user is None:
#         raise HTTPException(404)
#     return user
#
#
# @app.delete("/api/users/{id}", response_model=User)
# async def delete_user_by_id(id: ObjectId):
#     user = await engine.find_one(User, User.id == id)
#     if user is None:
#         raise HTTPException(404)
#     await engine.delete(user)
#     return user


