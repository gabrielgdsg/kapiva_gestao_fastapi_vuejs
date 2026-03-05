"""
Pedidos Chegando (Incoming Orders) API.

Uses Gmail (OAuth2) + PDF extraction + Gemini/Claude. Orders stored in JSON file
(backend/uploads/pedidos_chegando.json) unless DB is configured.
"""
import io
import logging
import os
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.api.pedidos_chegando.store import load_orders, save_orders, append_order, update_order, delete_order, save_order_pdf, get_order_pdf_path
from app.api.pedidos_chegando.store_mongo import (
    use_mongo,
    load_orders_mongo,
    save_orders_mongo,
    append_order_mongo,
    update_order_mongo,
    delete_order_mongo,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _base_ref(ref: str) -> str:
    """Extract base reference (e.g. H3782 from H3782-0001)."""
    if not ref or not isinstance(ref, str):
        return ""
    parts = ref.strip().split("-")
    if len(parts) > 1 and parts[-1] and len(parts[-1]) <= 4 and parts[-1].isdigit():
        return "-".join(parts[:-1])
    return ref


def _is_excluded_subject(subject: str, settings) -> bool:
    """True if subject matches exclude patterns (e.g. fatura CDL, fatura referente)."""
    if not subject or not isinstance(subject, str):
        return False
    excl = (getattr(settings, "SUBJECT_EXCLUDE_KEYWORDS", "fatura cdl,fatura referente,notificacao de emissao de boleto bancario,boleto bancario") or "").split(",")
    s = subject.lower().strip()
    for kw in excl:
        if kw.strip() and kw.strip() in s:
            return True
    return False


def _orders_for_frontend(orders: list, settings=None) -> list:
    """Map stored orders to the shape expected by PedidosChegando.vue."""
    if orders is None or not isinstance(orders, list):
        return []
    out = []
    for o in orders:
        products = []
        for p in o.get("products") or []:
            products.append({
                "ref": p.get("ref", ""),
                "name": p.get("name", ""),
                "color": p.get("color", ""),
                "hex": p.get("hex", "#888"),
                "qty": int(p.get("qty", 0)),
                "unit": p.get("unit", "par"),
                "sizes": p.get("sizes") or {},
                "img": p.get("img", ""),
                "src": p.get("src", "auto"),
                "flag": bool(p.get("flag", False)),
                "feedback": p.get("feedback") or {},
            })
        total_pairs = sum(pr.get("qty", 0) for pr in products)
        delivery = o.get("delivery_date") or o.get("deliveryMonth", "")
        if delivery and len(delivery) == 10:  # YYYY-MM-DD
            try:
                dt = datetime.strptime(delivery, "%Y-%m-%d")
                delivery = dt.strftime("%B %Y").replace("January", "Janeiro").replace("February", "Fevereiro").replace("March", "Março").replace("April", "Abril").replace("May", "Maio").replace("June", "Junho").replace("July", "Julho").replace("August", "Agosto").replace("September", "Setembro").replace("October", "Outubro").replace("November", "Novembro").replace("December", "Dezembro")
            except Exception:
                pass
        out.append({
            "id": o.get("id"),
            "brand": o.get("brand", ""),
            "ref": o.get("order_ref", o.get("ref", "")),
            "status": o.get("status", "needs-review"),
            "source": o.get("source", "email"),
            "deliveryMonth": delivery or o.get("deliveryMonth", "—"),
            "totalPairs": total_pairs or o.get("totalPairs", 0),
            "products": products,
            "invoice": o.get("invoice", False),
            "invDate": o.get("invDate", ""),
            "city": o.get("city", ""),
            "estArrival": o.get("estArrival", ""),
            "track": o.get("track", ""),
            "hist": o.get("hist", False),
            "provider": o.get("provider", ""),
            "conf": o.get("confidence", o.get("conf", 0.8)),
            "flagged": o.get("flagged", 0),
            "subjectSnippet": o.get("subject_snippet", ""),
        })
    return out


@router.get("/api/pedidos-chegando")
async def list_pedidos_chegando():
    """List incoming orders from store. Excludes fatura CDL / fatura referente (NF-e go to separate tab)."""
    try:
        if use_mongo(settings):
            orders = await load_orders_mongo(settings)
        else:
            orders = load_orders(settings)
        # Filter out non-pedidos (monthly invoices, CDL, etc.)
        orders = [o for o in orders if not _is_excluded_subject(o.get("subject_snippet", "") or o.get("subjectSnippet", ""), settings)]
        return _orders_for_frontend(orders, settings)
    except Exception as e:
        logger.exception("List pedidos-chegando: %s", e)
        return []


class OrderPatchBody(BaseModel):
    status: Optional[str] = None
    brand: Optional[str] = None
    order_ref: Optional[str] = None
    subject_snippet: Optional[str] = None
    provider: Optional[str] = None


class ProductFeedbackBody(BaseModel):
    """Per-product feedback. base_ref+color identify the product group."""
    base_ref: str = ""
    color: str = ""
    img_ok: Optional[bool] = None
    ref_ok: Optional[bool] = None
    color_ok: Optional[bool] = None
    sizes_ok: Optional[bool] = None


@router.patch("/api/pedidos-chegando/order/{order_id}")
async def patch_order(order_id: int, body: OrderPatchBody):
    """Update order (status, brand, order_ref, subject_snippet)."""
    try:
        updates = body.dict(exclude_unset=True)
        if not updates:
            return {"ok": False, "error": "No updates"}
        if use_mongo(settings):
            ok = await update_order_mongo(settings, order_id, updates)
        else:
            ok = update_order(settings, order_id, updates)
        if ok:
            return {"ok": True}
        return {"ok": False, "error": "Order not found"}
    except Exception as e:
        logger.exception("Patch order: %s", e)
        return {"ok": False, "error": str(e)}


@router.delete("/api/pedidos-chegando/order/{order_id}")
async def remove_order(order_id: int):
    """Delete an order permanently (removes from store)."""
    try:
        if use_mongo(settings):
            ok = await delete_order_mongo(settings, order_id)
        else:
            ok = delete_order(settings, order_id)
        if ok:
            return {"ok": True}
        return {"ok": False, "error": "Order not found"}
    except Exception as e:
        logger.exception("Delete order: %s", e)
        return {"ok": False, "error": str(e)}


@router.patch("/api/pedidos-chegando/order/{order_id}/product-feedback")
async def patch_product_feedback(order_id: int, body: ProductFeedbackBody):
    """Update feedback for products matching base_ref+color. Feedback: img_ok, ref_ok, color_ok, sizes_ok (true/false)."""
    try:
        if use_mongo(settings):
            orders = await load_orders_mongo(settings)
        else:
            orders = load_orders(settings)
        order = next((o for o in orders if o.get("id") == order_id), None)
        if not order:
            return {"ok": False, "error": "Pedido não encontrado"}
        base_ref = (body.base_ref or "").strip()
        color = (body.color or "").strip() or "—"
        if not base_ref:
            return {"ok": False, "error": "base_ref é obrigatório"}
        feedback = {
            k: v for k, v in {
                "img_ok": body.img_ok,
                "ref_ok": body.ref_ok,
                "color_ok": body.color_ok,
                "sizes_ok": body.sizes_ok,
            }.items() if v is not None
        }
        if not feedback:
            return {"ok": False, "error": "Nenhum feedback informado"}
        updated = 0
        for p in order.get("products") or []:
            pr_base = _base_ref(p.get("ref", "") or "")
            pr_color = (p.get("color", "") or "").strip() or "—"
            if pr_base == base_ref and pr_color == color:
                p["feedback"] = {**(p.get("feedback") or {}), **feedback}
                updated += 1
        if updated == 0:
            return {"ok": False, "error": "Nenhum produto encontrado com essa ref/cor"}
        if use_mongo(settings):
            await save_orders_mongo(settings, orders)
        else:
            save_orders(settings, orders)
        return {"ok": True, "updated": updated}
    except Exception as e:
        logger.exception("Patch product feedback: %s", e)
        return {"ok": False, "error": str(e)}


@router.post("/api/pedidos-chegando/order/{order_id}/re-extract-images")
async def re_extract_images_from_pdf(order_id: int):
    """Re-extract images from stored PDF and update products. Uses smarter filtering (size analysis, discard logos/singletons)."""
    path = get_order_pdf_path(settings, order_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="PDF não disponível para este pedido")
    try:
        if use_mongo(settings):
            orders = await load_orders_mongo(settings)
        else:
            orders = load_orders(settings)
        order = next((o for o in orders if o.get("id") == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        products = order.get("products") or []
        expected_count = len(products)

        content = path.read_bytes()
        from extraction.pdf_images import pdf_to_images_as_base64
        imgs = pdf_to_images_as_base64(content, max_images=20, expected_count=expected_count)
        logger.info("Re-extract images order_id=%s: images_found=%s expected=%s", order_id, len(imgs), expected_count)

        # Assign one image per displayed group (baseRef|color), not per flat product
        seen_groups = {}
        for idx, p in enumerate(products):
            base = _base_ref(p.get("ref", "") or "")
            color = (p.get("color", "") or "").strip() or "—"
            gkey = f"{base}|{color}"
            if gkey not in seen_groups:
                seen_groups[gkey] = len(seen_groups)
            img_idx = min(seen_groups[gkey], len(imgs) - 1) if imgs else 0
            if imgs:
                p["img"] = imgs[img_idx].get("data_url", "") or ""
                p["src"] = "pdf"

        if use_mongo(settings):
            ok = await update_order_mongo(settings, order_id, {"products": order.get("products", [])})
            logger.info("Re-extract images: updated in MongoDB ok=%s", ok)
        else:
            save_orders(settings, orders)
            logger.info("Re-extract images: saved to JSON")

        # Return updated order so frontend can refresh without full list fetch
        order_for_fe = next(
            (x for x in _orders_for_frontend([order], settings)),
            None,
        )
        img_lens = [len(str(p.get("img", ""))) for p in (order_for_fe.get("products") or [])]
        logger.info("Re-extract images: returning order with product img lengths %s", img_lens)
        return {"ok": True, "updated": len(products), "images_found": len(imgs), "order": order_for_fe}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Re-extract images: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/pedidos-chegando/order/{order_id}/re-extract-feedback")
async def re_extract_feedback_only(order_id: int):
    """
    Re-extract only the fields marked as wrong in feedback (img_ok/ref_ok/color_ok/sizes_ok === false).
    Uses PDF + AI extraction for ref/color/sizes; image extraction for img.
    """
    path = get_order_pdf_path(settings, order_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="PDF não disponível para este pedido")
    try:
        if use_mongo(settings):
            orders = await load_orders_mongo(settings)
        else:
            orders = load_orders(settings)
        order = next((o for o in orders if o.get("id") == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        products = order.get("products") or []
        if not products:
            raise HTTPException(status_code=400, detail="Pedido sem itens")

        content = path.read_bytes()
        needs_img = []
        needs_ref_color_sizes = []
        for idx, p in enumerate(products):
            fb = p.get("feedback") or {}
            if fb.get("img_ok") is False:
                needs_img.append(idx)
            if fb.get("ref_ok") is False or fb.get("color_ok") is False or fb.get("sizes_ok") is False:
                needs_ref_color_sizes.append(idx)

        if not needs_img and not needs_ref_color_sizes:
            order_for_fe = next(
                (x for x in _orders_for_frontend([order], settings)),
                None,
            )
            return {
                "ok": True,
                "updated": 0,
                "message": "Nenhum campo marcado como incorreto. Marque ✗ nos itens que precisam correção.",
                "order": order_for_fe,
            }

        updated_count = 0

        # Re-extract images only for products with img_ok === false (update whole group)
        if needs_img:
            from extraction.pdf_images import pdf_to_images_as_base64
            imgs = pdf_to_images_as_base64(content, max_images=20, expected_count=len(products))
            groups_needing_img = set()
            for idx in needs_img:
                if idx < len(products):
                    p = products[idx]
                    base = _base_ref(p.get("ref", "") or "")
                    color = (p.get("color", "") or "").strip() or "—"
                    groups_needing_img.add((base, color))
            seen_groups = {}
            for p in products:
                base = _base_ref(p.get("ref", "") or "")
                color = (p.get("color", "") or "").strip() or "—"
                gkey = (base, color)
                if gkey not in seen_groups:
                    seen_groups[gkey] = len(seen_groups)
                if gkey in groups_needing_img and imgs:
                    img_idx = min(seen_groups[gkey], len(imgs) - 1)
                    p["img"] = imgs[img_idx].get("data_url", "") or ""
                    p["src"] = "pdf"
                    updated_count += 1

        # Re-extract ref/color/sizes via AI for products with feedback
        if needs_ref_color_sizes:
            gemini_key = (getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY") or "").strip()
            if not gemini_key:
                raise HTTPException(status_code=400, detail="GEMINI_API_KEY necessário para re-extrair ref/cor/grade")
            conf_threshold = float(getattr(settings, "CONFIDENCE_THRESHOLD", 0.75) or 0.75)
            for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN", "GEMINI_API_KEY", "GEMINI_MODEL"):
                v = getattr(settings, k, None) or os.environ.get(k)
                if v is not None and str(v).strip():
                    os.environ[k] = str(v).strip()

            text = ""
            try:
                import fitz
                doc = fitz.open(stream=content, filetype="pdf")
                for page in doc:
                    text += page.get_text()
                doc.close()
            except Exception:
                pass
            if not (text and len(text.strip()) > 50):
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(io.BytesIO(content))
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            text += t
                except Exception:
                    pass

            from extraction.ai_extractor import extract_order_from_text, extract_order_from_pdf
            from extraction.validator import validate_order_data

            text_ok = text and len(text.strip()) > 50
            if text_ok:
                data = extract_order_from_text(
                    text,
                    gemini_api_key=gemini_key,
                    anthropic_api_key=getattr(settings, "ANTHROPIC_API_KEY", None) or os.environ.get("ANTHROPIC_API_KEY"),
                    confidence_threshold=conf_threshold,
                )
            else:
                data = extract_order_from_pdf(content, gemini_api_key=gemini_key, confidence_threshold=conf_threshold)
            data = validate_order_data(data)
            new_items = data.get("items") or []

            for idx in needs_ref_color_sizes:
                if idx >= len(new_items):
                    continue
                p = products[idx]
                fb = p.get("feedback") or {}
                new_it = new_items[idx]
                if fb.get("ref_ok") is False and new_it.get("ref"):
                    p["ref"] = str(new_it.get("ref", "")).strip() or p.get("ref", "")
                    updated_count += 1
                if fb.get("color_ok") is False and new_it.get("color") is not None:
                    p["color"] = str(new_it.get("color", "")).strip() or p.get("color", "")
                    updated_count += 1
                if fb.get("sizes_ok") is False and isinstance(new_it.get("sizes"), dict):
                    p["sizes"] = {str(k): int(v) for k, v in new_it["sizes"].items() if v and int(v) > 0}
                    p["qty"] = sum(p["sizes"].values())
                    updated_count += 1

        if use_mongo(settings):
            ok = await update_order_mongo(settings, order_id, {"products": order.get("products", [])})
            logger.info("Re-extract feedback: updated in MongoDB ok=%s", ok)
        else:
            save_orders(settings, orders)

        order_for_fe = next(
            (x for x in _orders_for_frontend([order], settings)),
            None,
        )
        return {
            "ok": True,
            "updated": updated_count,
            "order": order_for_fe,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Re-extract feedback: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/pedidos-chegando/feedback-analytics")
async def feedback_analytics():
    """Aggregate feedback by brand: which brands have more errors, which fields fail most often."""
    try:
        if use_mongo(settings):
            orders = await load_orders_mongo(settings)
        else:
            orders = load_orders(settings)
        orders = [o for o in orders if not _is_excluded_subject(o.get("subject_snippet", "") or o.get("subjectSnippet", ""), settings)]

        by_brand = {}
        total_orders_with_feedback = 0
        total_products_with_feedback = 0

        for o in orders:
            brand = (o.get("brand") or "").strip() or "—"
            if brand not in by_brand:
                by_brand[brand] = {
                    "orders_count": 0,
                    "products_count": 0,
                    "img_ok_false": 0,
                    "ref_ok_false": 0,
                    "color_ok_false": 0,
                    "sizes_ok_false": 0,
                    "products_with_feedback": 0,
                }
            by_brand[brand]["orders_count"] += 1

            order_has_feedback = False
            for p in o.get("products") or []:
                by_brand[brand]["products_count"] += 1
                fb = p.get("feedback") or {}
                if not fb:
                    continue
                order_has_feedback = True
                by_brand[brand]["products_with_feedback"] += 1
                total_products_with_feedback += 1
                if fb.get("img_ok") is False:
                    by_brand[brand]["img_ok_false"] += 1
                if fb.get("ref_ok") is False:
                    by_brand[brand]["ref_ok_false"] += 1
                if fb.get("color_ok") is False:
                    by_brand[brand]["color_ok_false"] += 1
                if fb.get("sizes_ok") is False:
                    by_brand[brand]["sizes_ok_false"] += 1

            if order_has_feedback:
                total_orders_with_feedback += 1

        # Sort brands by total errors (desc)
        def _err_sum(b):
            return b["img_ok_false"] + b["ref_ok_false"] + b["color_ok_false"] + b["sizes_ok_false"]

        sorted_brands = sorted(by_brand.items(), key=lambda x: _err_sum(x[1]), reverse=True)

        return {
            "by_brand": dict(sorted_brands),
            "summary": {
                "total_orders": len(orders),
                "total_orders_with_feedback": total_orders_with_feedback,
                "total_products_with_feedback": total_products_with_feedback,
            },
        }
    except Exception as e:
        logger.exception("Feedback analytics: %s", e)
        return {"by_brand": {}, "summary": {}}


@router.post("/api/pedidos-chegando/cleanup-excluded")
async def cleanup_excluded_orders():
    """Remove from store orders that match SUBJECT_EXCLUDE_KEYWORDS (fatura CDL, etc.). Returns count removed."""
    try:
        if use_mongo(settings):
            orders = await load_orders_mongo(settings)
        else:
            orders = load_orders(settings)
        kept = [o for o in orders if not _is_excluded_subject(o.get("subject_snippet", ""), settings)]
        removed = len(orders) - len(kept)
        if removed > 0:
            if use_mongo(settings):
                await save_orders_mongo(settings, kept)
            else:
                save_orders(settings, kept)
        return {"ok": True, "removed": removed, "orders": _orders_for_frontend(kept, settings)}
    except Exception as e:
        logger.exception("Cleanup excluded: %s", e)
        return {"ok": False, "error": str(e), "removed": 0}


@router.get("/api/pedidos-chegando/order/{order_id}/pdf")
async def get_order_pdf(order_id: int):
    """Serve saved PDF for an order (if stored during sync)."""
    path = get_order_pdf_path(settings, order_id)
    if not path:
        raise HTTPException(status_code=404, detail="PDF não disponível para este pedido")
    return FileResponse(path, media_type="application/pdf", filename=f"pedido-{order_id}.pdf")


@router.post("/api/pedidos-chegando/sync")
async def sync_pedidos_chegando(backfill_from: Optional[str] = None):
    """Fetch Gmail (pedido/NF-e), extract PDFs with Gemini, save orders. backfill_from=YYYY-MM-DD for importar histórico."""
    logger.info("pedidos-chegando sync: request received backfill_from=%s", backfill_from)
    log = []
    try:
        if use_mongo(settings):
            orders_snapshot = await load_orders_mongo(settings)
        else:
            orders_snapshot = load_orders(settings)
    except Exception as e:
        logger.exception("Load orders: %s", e)
        orders_snapshot = []

    client_id = getattr(settings, "GOOGLE_CLIENT_ID", None) or os.environ.get("GOOGLE_CLIENT_ID")
    refresh_token = getattr(settings, "GOOGLE_REFRESH_TOKEN", None) or os.environ.get("GOOGLE_REFRESH_TOKEN")
    if not (client_id and refresh_token):
        return {
            "log": ["Configure GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET e GOOGLE_REFRESH_TOKEN no backend/.env. Rode ./run_auth.sh no backend para obter o refresh token."],
            "orders": _orders_for_frontend([o for o in orders_snapshot if not _is_excluded_subject(o.get("subject_snippet", ""), settings)], settings),
        }

    # Set env so gmail.oauth2 and extractor can use them (settings + os.environ for Docker)
    for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN", "GMAIL_ADDRESS", "GEMINI_MODEL"):
        v = getattr(settings, k, None) or os.environ.get(k)
        if v is not None and str(v).strip():
            os.environ[k] = str(v).strip()

    try:
        from gmail.poller import fetch_emails
        # Only pedidos (purchase orders) — NF-e/fatura go to a separate tab
        subject_kw = (getattr(settings, "SUBJECT_KEYWORDS", "pedido,order,encomenda,compra,notificacao") or "").split(",")
        keywords = list(dict.fromkeys(k.strip() for k in subject_kw if k.strip()))
        if not keywords:
            keywords = ["pedido"]
        max_msgs = 200 if backfill_from else 100
        since_date = backfill_from if backfill_from else None
        if since_date:
            log.append(f"Importação histórica desde {since_date}…")
        log.append(f"Buscando e-mails no Gmail (termos no assunto: {', '.join(keywords[:10])}{'…' if len(keywords) > 10 else ''})…")
        logger.info("pedidos-chegando sync: calling fetch_emails since_date=%s max_messages=%s", since_date, max_msgs)
        emails = fetch_emails(keywords, max_messages=max_msgs, settings=settings, since_date=since_date)
        logger.info("pedidos-chegando sync: fetch_emails returned %s emails", len(emails))
        log.append(f"Encontrados {len(emails)} e-mail(s).")
        if not emails:
            log.append("Nenhum e-mail com esses termos no assunto. Verifique no Gmail se há mensagens com algum deles (ex.: pedido, NF-e, order). Se estiverem em outra pasta, ative 'Mostrar na IMAP' em [Gmail]/All Mail.")

        gemini_key = (getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY") or "").strip()
        conf_threshold = float(getattr(settings, "CONFIDENCE_THRESHOLD", 0.75) or 0.75)
        logger.info("pedidos-chegando sync: GEMINI_API_KEY presente=%s", bool(gemini_key))
        if not gemini_key:
            log.append("Aviso: GEMINI_API_KEY não encontrado. Defina no backend/.env e reinicie o container (docker restart kapiva-backend-dev).")

        pdf_count = sum(len(em.get("pdf_attachments") or []) for em in emails)
        if pdf_count == 0 and emails:
            log.append("Nenhum anexo PDF encontrado nesses e-mails. Pedidos com PDF serão extraídos quando houver.")

        # Build set of already-imported gmail_uids — skip Gemini for these (saves API calls on re-sync)
        skip_already = getattr(settings, "PEDIDOS_SKIP_ALREADY_IMPORTED", True)
        existing_uids = set()
        if skip_already:
            for o in orders_snapshot:
                uid_val = o.get("gmail_uid")
                if uid_val is not None:
                    existing_uids.add(uid_val)
                    existing_uids.add(str(uid_val))
                    try:
                        existing_uids.add(int(uid_val))
                    except (TypeError, ValueError):
                        pass
            unique_count = len(set(int(u) for u in existing_uids if str(u).isdigit()))
            if unique_count > 0:
                log.append(f"Já importados: {unique_count} e-mail(s). Pulando para economizar chamadas à API.")
        skipped_count = 0

        # Limit how many PDFs we send to Gemini in this sync (for testing: set to 2–3, then remove for full sync)
        max_pdfs_raw = (getattr(settings, "PEDIDOS_CHEGANDO_MAX_PDFS", None) or os.environ.get("PEDIDOS_CHEGANDO_MAX_PDFS") or "").strip()
        try:
            max_pdfs = int(max_pdfs_raw) if max_pdfs_raw else 0
        except ValueError:
            max_pdfs = 0
        if max_pdfs > 0:
            log.append(f"Modo teste: extraindo no máximo {max_pdfs} PDF(s) nesta sincronização (PEDIDOS_CHEGANDO_MAX_PDFS). Remova ou defina 0 para processar todos.")
        pdfs_processed = 0

        for em in emails:
            uid = em.get("uid")
            subject = em.get("subject", "")
            # Email Subject can be a Header object (not subscriptable); ensure string
            subject_str = str(subject) if subject else ""
            # Skip non-pedidos (fatura CDL, fatura referente, etc.) — NF-e go to separate tab
            if _is_excluded_subject(subject_str, settings):
                log.append(f"Pulando (não é pedido): {subject_str[:50]}…")
                continue
            # Skip already-imported emails — no Gemini call (saves API usage on re-sync)
            if skip_already and uid is not None and uid in existing_uids:
                skipped_count += 1
                continue
            pdfs = em.get("pdf_attachments") or []
            if not pdfs:
                continue
            for att in pdfs:
                content = att.get("content")
                if not content:
                    continue
                if max_pdfs > 0 and pdfs_processed >= max_pdfs:
                    log.append(f"Pulando PDF (limite de teste {max_pdfs} atingido): {att.get('filename', '?')}")
                    continue
                log.append(f"Processando PDF: {att.get('filename', '?')} (e-mail: {subject_str[:50]}…)")
                try:
                    text = ""
                    try:
                        import fitz
                        doc = fitz.open(stream=content, filetype="pdf")
                        for p in doc:
                            text += p.get_text()
                        doc.close()
                    except Exception:
                        pass
                    if not (text and text.strip()):
                        try:
                            from pypdf import PdfReader
                            reader = PdfReader(io.BytesIO(content))
                            for p in reader.pages:
                                t = p.extract_text()
                                if t:
                                    text += t
                        except Exception:
                            pass
                    from extraction.ai_extractor import (
                        extract_order_from_text,
                        extract_order_from_pdf,
                    )
                    from extraction.validator import validate_order_data

                    model_used = (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip() or "gemini-2.5-flash"
                    text_ok = text and len(text.strip()) > 50
                    if text_ok:
                        log.append(f"  → Extraindo do texto (%s chars, modelo %s)" % (len(text.strip()), model_used))
                        data = extract_order_from_text(
                            text,
                            gemini_api_key=gemini_key,
                            anthropic_api_key=getattr(settings, "ANTHROPIC_API_KEY", None) or os.environ.get("ANTHROPIC_API_KEY"),
                            confidence_threshold=conf_threshold,
                        )
                    else:
                        log.append("  → Texto do PDF vazio/falha; enviando PDF ao Gemini (visão, modelo %s)." % model_used)
                        data = extract_order_from_pdf(
                            content,
                            gemini_api_key=gemini_key,
                            confidence_threshold=conf_threshold,
                        )
                    pdfs_processed += 1
                    raw_count = len(data.get("items") or data.get("products") or [])
                    data = validate_order_data(data)
                    items = data.get("items") or []
                    total = sum(i.get("qty", 0) for i in items)
                    err = data.get("error")
                    logger.info("pedidos-chegando sync: Gemini raw=%s itens, após validação=%s, error=%s", raw_count, len(items), err)

                    # Extract images from PDF and attach to products (smarter filtering by size)
                    try:
                        from extraction.pdf_images import pdf_to_images_as_base64
                        imgs = pdf_to_images_as_base64(content, max_images=20, expected_count=len(items))
                        for idx, it in enumerate(items):
                            if imgs:
                                img_idx = min(idx, len(imgs) - 1)
                                it["img"] = imgs[img_idx].get("data_url", "") or ""
                                it["src"] = "pdf"
                    except Exception as img_err:
                        logger.debug("PDF image extraction: %s", img_err)

                    if not items and not (data.get("brand") or data.get("order_ref")):
                        if err:
                            log.append(f"  → Extração sem dados: {err}")
                        elif not gemini_key:
                            log.append(f"  → Extração sem dados (adicione GEMINI_API_KEY no backend/.env)")
                        elif raw_count and not items:
                            log.append(f"  → Gemini retornou {raw_count} itens mas foram filtrados (ref/name/qty). Ajuste o validator se necessário.")
                        else:
                            log.append(f"  → Extração sem itens (PDF pode ser só imagem ou texto não reconhecido)")
                        continue
                    auto_confirm = getattr(settings, "PEDIDOS_AUTO_CONFIRM", False)
                    status = "confirmed" if (auto_confirm and (data.get("confidence") or 0) >= conf_threshold) else "needs-review"
                    delivery = data.get("delivery_date") or ""
                    order = {
                        "id": None,
                        "gmail_uid": uid,
                        "brand": data.get("brand", ""),
                        "order_ref": data.get("order_ref", ""),
                        "status": status,
                        "source": "email",
                        "delivery_date": delivery,
                        "deliveryMonth": delivery,
                        "totalPairs": total,
                        "confidence": data.get("confidence", 0),
                        "provider": "Gemini",
                        "subject_snippet": subject_str[:60].strip() if subject_str else "",
                        "products": [{"ref": i.get("ref"), "name": i.get("name"), "color": i.get("color"), "qty": i.get("qty", 0), "unit": i.get("unit", "par"), "sizes": i.get("sizes") or {}, "hex": "#888", "img": i.get("img", ""), "src": i.get("src", "pdf"), "flag": False} for i in items],
                    }
                    if use_mongo(settings):
                        await append_order_mongo(settings, order)
                    else:
                        append_order(settings, order)
                    save_order_pdf(settings, order["id"], content)
                    log.append(f"  → Pedido {data.get('order_ref', '?')} ({data.get('brand', '?')}): {len(items)} itens, conf. {data.get('confidence', 0):.0%}")
                except Exception as e:
                    logger.exception("Extract PDF: %s", e)
                    log.append(f"  → Erro: {e}")

        if skipped_count > 0:
            log.append(f"→ {skipped_count} e-mail(s) já importado(s), pulados (sem chamada à API).")

        try:
            if use_mongo(settings):
                orders = await load_orders_mongo(settings)
            else:
                orders = load_orders(settings)
            orders = [o for o in orders if not _is_excluded_subject(o.get("subject_snippet", ""), settings)]
            return {"log": log, "orders": _orders_for_frontend(orders, settings)}
        except Exception as e2:
            logger.exception("Load orders after sync: %s", e2)
            filtered = [o for o in orders_snapshot if not _is_excluded_subject(o.get("subject_snippet", ""), settings)]
            return {"log": log, "orders": _orders_for_frontend(filtered, settings)}
    except Exception as e:
        logger.exception("Sync failed: %s", e)
        filtered = [o for o in orders_snapshot if not _is_excluded_subject(o.get("subject_snippet", ""), settings)]
        return {
            "log": log + [f"Erro: {e}"],
            "orders": _orders_for_frontend(filtered, settings),
        }
