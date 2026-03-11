from typing import List
import sys
from pathlib import Path

# Add project root and backend to Python path (db_mongo, gmail, extraction)
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
# In Docker, db_mongo is at /db_mongo; ensure its parent is on path
if Path("/db_mongo").exists():
    if "/" not in sys.path:
        sys.path.insert(0, "/")
for p in (str(project_root), str(backend_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

# from fastapi_offline import FastAPIOffline
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.api.comissao import api_comissao
from app.api.financeiro import api_caixa
from app.api.levantamentos import api_levantamentos
from app.api.estoque import api_estoque
from app.db_postgres.connection import PostgresDatabase
from app.config import settings
# from app.api.models import User
from db_mongo.database import engine, ObjectId
from db_mongo.database import init_db
from app.api.vendas.api_vendas import router as vendas_router
from app.api.faturamento.api_faturamento import router as faturamento_router
from app.api.vendedor.api_vendedor import router as vendedor_router
from app.api.pedidos_chegando import router as pedidos_chegando_router
from app.api.clientes.api_clientes import router as clientes_router
from app.core.logging import setup_logging, get_logger
from pathlib import Path

# Initialize logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)

# app = FastAPIOffline()
app = FastAPI()

app.include_router(api_levantamentos.router)
app.include_router(api_estoque.router)
app.include_router(api_comissao.router)
app.include_router(api_caixa.router)
# Register vendedor_router BEFORE vendas_router to avoid route conflicts
# (vendas_router has /api/vendedor/{cod_vendedor} which would match /api/vendedor/ativos)
app.include_router(vendedor_router)
app.include_router(faturamento_router)
app.include_router(pedidos_chegando_router)
app.include_router(clientes_router)
app.include_router(vendas_router)

# Initialize database connection pool (non-fatal so app can start when DB unreachable, e.g. in Docker)
try:
    PostgresDatabase.initialise(user=settings.POSTGRES_USER, password=settings.POSTGRES_PASSWORD,
                                database=settings.POSTGRES_DATABASE, host=settings.POSTGRES_HOST,
                                port=settings.POSTGRES_PORT)
    logger.info(f"Database connection pool initialized for {settings.POSTGRES_DATABASE}")
except Exception as e:
    logger.warning(f"PostgreSQL not available: {e}. App will start; Comissão/Levantamentos/Estoque etc. will fail until DB is reachable.")

# REMOVED: Hardcoded credentials from commented code (security best practice)
# Database connection is now configured via environment variables in settings
# See develop_pycharm.env, develop_docker.env, or prod.env for configuration


# CORS Configuration - configurable via environment variable
# Default: safe development origins. Override via ALLOWED_ORIGINS env var
# For production, set ALLOWED_ORIGINS to specific domains (comma-separated)
# Note: Using '*' allows all origins - security risk in production!
origins_str = getattr(settings, 'ALLOWED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080')
if origins_str == '*':
    origins = ['*']  # Keep backward compatibility if explicitly set to '*'
else:
    origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# PERFORMANCE: Gzip compression for API responses
# Compresses responses >1KB by 60-80%, significantly faster data transfer
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # Only compress responses larger than 1KB
)


def _mongo_host_for_log(url: str) -> str:
    """Return a safe log string (e.g. mongodb://***@192.168.1.170:27017) for debugging."""
    if not url or "@" not in url:
        return url.split("?")[0] if url else "(not set)"
    pre, rest = url.split("@", 1)
    return "***@" + rest.split("?")[0]


@app.on_event("startup")
async def start_db():
    """Initialize MongoDB on application startup."""
    try:
        logger.info("MongoDB connecting to %s (metas/saved config use this DB)", _mongo_host_for_log(settings.MONGODB_URL))
        await init_db()
        logger.info("MongoDB database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        logger.warning("Continuing without MongoDB - some features may not work")
        # Don't raise - allow server to start even if MongoDB fails
        # This allows the app to work with just PostgreSQL


# Mount frontend static files AFTER all API routes and middleware
# This ensures API routes take precedence over static file serving
frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist_path), html=True), name="static")
    logger.info(f"Serving frontend static files from {frontend_dist_path}")
else:
    logger.warning(f"Frontend dist directory not found at {frontend_dist_path}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run('main:app', port=80, host=settings.UVICORN_HOST, log_level="info", reload=True, debug=True)
#     # uvicorn.run(app=app, host="0.0.0.0", port=80, debug=True)


if __name__ == "__main__":
    import asyncio
    import uvicorn

    loop = asyncio.get_event_loop()
    config = uvicorn.Config(app=app, port=8000, loop=loop, host=settings.UVICORN_HOST, log_level="info", reload=True)
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
