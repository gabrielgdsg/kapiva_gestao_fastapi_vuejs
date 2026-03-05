# extraction/validator.py — Simple validation for extracted order data
from typing import Any, Dict, List


def validate_order_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure required fields exist and types are correct. Returns cleaned dict.
    """
    brand = (data.get("brand") or "").strip() or "Desconhecida"
    order_ref = (data.get("order_ref") or "").strip() or "—"
    delivery_date = (data.get("delivery_date") or "").strip() or None
    confidence = float(data.get("confidence", 0))

    items = []
    raw_items = data.get("items") or data.get("products") or []
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        ref = str(it.get("ref") or it.get("reference") or "").strip()
        name = str(it.get("name") or it.get("description") or it.get("desc") or "").strip()
        color = str(it.get("color") or it.get("cor") or "").strip()
        try:
            qty = int(it.get("qty") or it.get("quantity") or it.get("quantidade") or 0)
        except (TypeError, ValueError):
            qty = 0
        unit = str(it.get("unit") or "par").strip().lower()
        if unit not in ("par", "unidade"):
            unit = "par" if not any(kw in (name or "").lower() for kw in ("bola", "ball", "mochila", "backpack", "bolsa", "bag", "boné", "cinto", "belt")) else "unidade"
        sizes = it.get("sizes") or it.get("grade") or {}
        if isinstance(sizes, dict):
            sizes = {str(k): int(v) for k, v in sizes.items() if v and int(v) > 0}
        else:
            sizes = {}
        if ref or name or qty > 0:
            items.append({"ref": ref or "—", "name": name or "—", "color": color or "—", "qty": max(0, qty), "unit": unit, "sizes": sizes})

    return {
        "brand": brand,
        "order_ref": order_ref,
        "delivery_date": delivery_date,
        "items": items,
        "confidence": min(1.0, max(0.0, confidence)),
    }
