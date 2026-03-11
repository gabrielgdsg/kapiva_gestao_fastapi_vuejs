"""
MongoDB sync for Levantamentos data.
Copies levantamentos from PostgreSQL to MongoDB for faster reads.
- Daily sync recommended (cron or scheduled task)
- Force sync via POST /api/levantamentos/sync
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from db_mongo.database import db
from .levantamentos_postgres import LevantamentoPostgres

logger = logging.getLogger(__name__)

COLLECTION = "levantamentos_cache"
MAX_AGE_HOURS = 24  # Consider cached data stale after 24h


def _doc_id(data_ini: str, data_fim: str, cod_marca: str) -> str:
    return f"{data_ini}|{data_fim}|{str(cod_marca)}"


def _format_row(row: tuple) -> list:
    """Format row for JSON/MongoDB serialization (dates to ISO, Decimal to float)."""
    row_list = list(row)
    for i in range(len(row_list)):
        v = row_list[i]
        if isinstance(v, Decimal):
            row_list[i] = float(v)
        elif i in (20, 21):
            if v and hasattr(v, 'strftime'):
                row_list[i] = v.strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif v and not isinstance(v, str):
                row_list[i] = str(v)
            elif not v:
                row_list[i] = '1900-01-01T00:00:00.000000'
        elif i == 29 and v:
            if hasattr(v, 'strftime'):
                row_list[i] = v.strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif not isinstance(v, str):
                row_list[i] = str(v)
    return row_list


async def sync_levantamentos(data_ini: str, data_fim: str, cod_marca: str) -> dict:
    """
    Sync levantamentos from PostgreSQL to MongoDB.
    Returns {ok, rows_synced, error}.
    """
    try:
        raw = LevantamentoPostgres.load_estoque_from_db(data_ini, data_fim, cod_marca)
        formatted = [_format_row(r) for r in raw]
        doc_id = _doc_id(data_ini, data_fim, cod_marca)
        doc = {
            "_id": doc_id,
            "data_ini": data_ini,
            "data_fim": data_fim,
            "cod_marca": str(cod_marca),
            "rows": formatted,
            "row_count": len(formatted),
            "synced_at": datetime.utcnow().isoformat() + "Z",
        }
        coll = db[COLLECTION]
        await coll.replace_one({"_id": doc_id}, doc, upsert=True)
        logger.info(f"Levantamentos sync: {doc_id} -> {len(formatted)} rows")
        return {"ok": True, "rows_synced": len(formatted), "doc_id": doc_id}
    except Exception as e:
        logger.exception("Levantamentos sync failed: %s", e)
        return {"ok": False, "rows_synced": 0, "error": str(e)}


async def get_from_mongo(data_ini: str, data_fim: str, cod_marca: str) -> Optional[List]:
    """
    Get levantamentos from MongoDB if available and fresh.
    Returns list of rows or None if not found/stale.
    """
    try:
        coll = db[COLLECTION]
        doc_id = _doc_id(data_ini, data_fim, cod_marca)
        doc = await coll.find_one({"_id": doc_id})
        if not doc or "rows" not in doc:
            return None
        synced_at = doc.get("synced_at")
        if synced_at:
            try:
                s = str(synced_at).replace("Z", "").split(".")[0]
                dt = datetime.fromisoformat(s)
                age_hours = (datetime.utcnow() - dt).total_seconds() / 3600
                if age_hours > MAX_AGE_HOURS:
                    logger.info(f"Levantamentos cache stale: {doc_id} (age={age_hours:.1f}h)")
                    return None
            except Exception:
                pass
        return doc["rows"]
    except Exception as e:
        logger.warning("get_from_mongo failed: %s", e)
        return None


async def ensure_indexes() -> None:
    """Create indexes for fast lookups."""
    try:
        coll = db[COLLECTION]
        await coll.create_index("synced_at")
        await coll.create_index([("data_ini", 1), ("data_fim", 1), ("cod_marca", 1)])
    except Exception as e:
        logger.warning("ensure_indexes: %s", e)
