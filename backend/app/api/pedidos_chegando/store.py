# Orders store (JSON file) for Pedidos Chegando — no DB migration required
import json
import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# Default path: backend/uploads/pedidos_chegando.json (or UPLOAD_DIR from settings)
def _store_path(settings) -> Path:
    base = getattr(settings, "UPLOAD_DIR", "./uploads") or "./uploads"
    base_path = Path(base)
    if not base_path.is_absolute():
        # __file__ = backend/app/api/pedidos_chegando/store.py -> backend_dir = backend
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        base_path = (backend_dir / base).resolve()
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / "pedidos_chegando.json"


def load_orders(settings) -> List[dict]:
    path = _store_path(settings)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning("Load orders failed: %s", e)
        return []


def save_orders(settings, orders: List[dict]) -> None:
    path = _store_path(settings)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Save orders failed: %s", e)


def append_order(settings, order: dict) -> List[dict]:
    orders = load_orders(settings)
    order_id = order.get("id")
    if not order_id:
        order["id"] = max([o.get("id", 0) for o in orders], default=0) + 1
    # Avoid duplicate by gmail_uid if present
    uid = order.get("gmail_uid")
    if uid is not None:
        orders = [o for o in orders if o.get("gmail_uid") != uid]
    orders.append(order)
    save_orders(settings, orders)
    return orders


def update_order(settings, order_id: int, updates: dict) -> bool:
    """Update an existing order by id. Returns True if found and saved."""
    orders = load_orders(settings)
    for o in orders:
        if o.get("id") == order_id:
            o.update(updates)
            save_orders(settings, orders)
            return True
    return False


def delete_order(settings, order_id: int) -> bool:
    """Remove an order by id. Returns True if found and deleted."""
    orders = load_orders(settings)
    new_orders = [o for o in orders if o.get("id") != order_id]
    if len(new_orders) == len(orders):
        return False
    save_orders(settings, new_orders)
    return True


def _pdf_dir(settings) -> Path:
    """Directory for storing PDFs: UPLOAD_DIR/pedidos_chegando_pdfs/."""
    base = getattr(settings, "UPLOAD_DIR", "./uploads") or "./uploads"
    base_path = Path(base)
    if not base_path.is_absolute():
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        base_path = (backend_dir / base).resolve()
    pdf_dir = base_path / "pedidos_chegando_pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    return pdf_dir


def save_order_pdf(settings, order_id: int, content: bytes) -> None:
    """Save PDF bytes for an order (for later open-in-browser)."""
    try:
        path = _pdf_dir(settings) / f"{order_id}.pdf"
        path.write_bytes(content)
    except Exception as e:
        logger.warning("Save order PDF failed: %s", e)


def get_order_pdf_path(settings, order_id: int) -> Optional[Path]:
    """Return path to saved PDF if it exists."""
    path = _pdf_dir(settings) / f"{order_id}.pdf"
    return path if path.exists() else None
