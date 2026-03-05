# MongoDB store for Pedidos Chegando — persistent across restarts and PCs
import asyncio
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

COLLECTION = "pedidos_chegando"


def _fallback_json(settings) -> bool:
    """True if we should fall back to JSON when MongoDB fails."""
    return getattr(settings, "MONGODB_FALLBACK_JSON", True)


def _get_collection(settings):
    """Get MongoDB collection for pedidos. Requires MONGODB_URL in settings."""
    from db_mongo.database import db
    return db[COLLECTION]


async def load_orders_mongo(settings) -> List[dict]:
    """Load all orders from MongoDB. Falls back to JSON if Mongo fails and MONGODB_FALLBACK_JSON=True."""
    try:
        coll = _get_collection(settings)
        cursor = coll.find({}).sort("id", 1)
        orders = []
        async for doc in cursor:
            doc.pop("_id", None)
            orders.append(doc)
        return orders
    except Exception as e:
        logger.warning("Load orders from MongoDB failed: %s", e)
        if _fallback_json(settings):
            try:
                from app.api.pedidos_chegando.store import load_orders
                orders = await asyncio.to_thread(load_orders, settings)
                logger.info("Fallback: loaded %d orders from JSON", len(orders))
                return orders
            except Exception as e2:
                logger.warning("Fallback to JSON failed: %s", e2)
        return []


async def save_orders_mongo(settings, orders: List[dict]) -> None:
    """Replace all orders in MongoDB. Falls back to JSON if Mongo fails."""
    try:
        coll = _get_collection(settings)
        await coll.delete_many({})
        if orders:
            clean = []
            for o in orders:
                c = dict(o)
                c.pop("_id", None)
                clean.append(c)
            await coll.insert_many(clean)
    except Exception as e:
        logger.warning("Save orders to MongoDB failed: %s", e)
        if _fallback_json(settings):
            try:
                from app.api.pedidos_chegando.store import save_orders
                await asyncio.to_thread(save_orders, settings, orders)
                logger.info("Fallback: saved %d orders to JSON", len(orders))
            except Exception as e2:
                logger.warning("Fallback to JSON failed: %s", e2)


async def append_order_mongo(settings, order: dict) -> List[dict]:
    """Append one order. Assign id if missing. Dedupe by gmail_uid."""
    orders = await load_orders_mongo(settings)
    order_id = order.get("id")
    if not order_id:
        order["id"] = max([o.get("id", 0) for o in orders], default=0) + 1
    uid = order.get("gmail_uid")
    if uid is not None:
        orders = [o for o in orders if o.get("gmail_uid") != uid]
    orders.append(order)
    try:
        coll = _get_collection(settings)
        if uid is not None:
            await coll.delete_many({"gmail_uid": uid})
        o_copy = dict(order)
        o_copy.pop("_id", None)
        await coll.insert_one(o_copy)
    except Exception as e:
        logger.warning("Append order to MongoDB failed: %s", e)
        if _fallback_json(settings):
            try:
                from app.api.pedidos_chegando.store import append_order
                orders = await asyncio.to_thread(append_order, settings, order)
                logger.info("Fallback: appended order to JSON")
            except Exception as e2:
                logger.warning("Fallback to JSON failed: %s", e2)
    return orders


async def update_order_mongo(settings, order_id: int, updates: dict) -> bool:
    """Update an existing order by id. Falls back to JSON if Mongo fails."""
    try:
        coll = _get_collection(settings)
        r = await coll.update_one({"id": order_id}, {"$set": updates})
        return r.modified_count > 0 or r.matched_count > 0
    except Exception as e:
        logger.warning("Update order in MongoDB failed: %s", e)
        if _fallback_json(settings):
            try:
                from app.api.pedidos_chegando.store import update_order
                return await asyncio.to_thread(update_order, settings, order_id, updates)
            except Exception as e2:
                logger.warning("Fallback to JSON failed: %s", e2)
        return False


async def delete_order_mongo(settings, order_id: int) -> bool:
    """Remove an order by id. Falls back to JSON if Mongo fails."""
    try:
        coll = _get_collection(settings)
        r = await coll.delete_one({"id": order_id})
        return r.deleted_count > 0
    except Exception as e:
        logger.warning("Delete order from MongoDB failed: %s", e)
        if _fallback_json(settings):
            try:
                from app.api.pedidos_chegando.store import delete_order
                return await asyncio.to_thread(delete_order, settings, order_id)
            except Exception as e2:
                logger.warning("Fallback to JSON failed: %s", e2)
        return False


def use_mongo(settings) -> bool:
    """True if MongoDB should be used for pedidos (MONGODB_URL configured)."""
    url = getattr(settings, "MONGODB_URL", None) or ""
    return bool(url and str(url).strip())
