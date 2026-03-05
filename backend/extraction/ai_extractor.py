# extraction/ai_extractor.py — Extract order data from PDF/text using Gemini (optional Claude fallback)
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Placeholder when PyMuPDF could not extract text
NO_TEXT_PLACEHOLDER = "(PDF sem texto extraível)"

# Default and fallbacks: try in order when API returns 404/not found. Prefer current free-tier models.
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-2.0-flash"]
# Deprecated/invalid model IDs (404 in v1beta); if GEMINI_MODEL is one of these, we use DEFAULT_GEMINI_MODEL
_DEPRECATED_GEMINI_MODELS = frozenset({"gemini-1.5-flash", "gemini-1.5-pro"})


def _infer_unit(name: str, unit_hint: str) -> str:
    """Return 'unidade' for balls, backpacks, etc.; 'par' for shoes/sandals."""
    if unit_hint and str(unit_hint).strip().lower() in ("un", "unidade", "unidades", "unit"):
        return "unidade"
    if unit_hint and str(unit_hint).strip().lower() in ("par", "pares", "pr"):
        return "par"
    n = (name or "").lower()
    if any(kw in n for kw in ("bola", "ball", "mochila", "backpack", "bkpk", "bolsa", "bag", "boné", "cinto", "belt", "óculos")):
        return "unidade"
    return "par"


def _normalize_gemini_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure items is a list of dicts with ref, name, color, qty, unit, sizes."""
    raw = data.get("items") or data.get("products") or []
    if not isinstance(raw, list):
        raw = []
    items = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        ref = str(it.get("ref") or it.get("reference") or "").strip()
        name = str(it.get("name") or it.get("description") or it.get("desc") or "").strip()
        color = str(it.get("color") or it.get("cor") or "").strip()
        try:
            qty = int(it.get("qty") or it.get("quantity") or it.get("quantidade") or 0)
        except (TypeError, ValueError):
            qty = 0
        unit_hint = it.get("unit") or it.get("unidade") or it.get("um") or ""
        unit = _infer_unit(name, unit_hint)
        sizes = it.get("sizes") or it.get("grade") or it.get("tamanhos") or {}
        if isinstance(sizes, dict):
            sizes = {str(k): int(v) for k, v in sizes.items() if v and int(v) > 0}
        else:
            sizes = {}
        items.append({
            "ref": ref or "—", "name": name or "—", "color": color or "—",
            "qty": max(0, qty), "unit": unit, "sizes": sizes
        })
    data["items"] = items
    if "products" in data:
        del data["products"]
    return data


def extract_order_from_text(
    text: str,
    gemini_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    confidence_threshold: float = 0.75,
) -> Dict[str, Any]:
    """
    Use Gemini to extract structured order data from email body or PDF text.
    Returns { brand, order_ref, delivery_date, items: [ { ref, name, color, qty } ], confidence }.
    If Gemini fails or confidence < threshold and anthropic key is set, tries Claude.
    """
    if not (gemini_api_key or anthropic_api_key):
        return {"confidence": 0.0, "error": "No API key (GEMINI_API_KEY or ANTHROPIC_API_KEY)"}

    payload = {
        "brand": "",
        "order_ref": "",
        "delivery_date": "",
        "items": [],
        "confidence": 0.0,
    }

    if gemini_api_key:
        try:
            payload = _extract_with_gemini(text, gemini_api_key)
        except Exception as e:
            logger.warning("Gemini extraction failed: %s", e)
            payload["error"] = str(e)

    if payload.get("confidence", 0) < confidence_threshold and anthropic_api_key:
        try:
            fallback = _extract_with_claude(text, anthropic_api_key)
            if fallback.get("confidence", 0) > payload.get("confidence", 0):
                payload = fallback
        except Exception as e:
            logger.warning("Claude extraction failed: %s", e)

    return payload


def _is_model_not_found_error(e: Exception) -> bool:
    err = str(e).lower()
    return "404" in err or "not found" in err or "not supported" in err


def _is_quota_error(e: Exception) -> bool:
    err = str(e).lower()
    return "429" in err or "quota" in err or "rate limit" in err


def _extract_with_gemini(text: str, api_key: str) -> Dict[str, Any]:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    raw_id = (os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model_id = DEFAULT_GEMINI_MODEL if raw_id in _DEPRECATED_GEMINI_MODELS else raw_id
    models_to_try = [model_id] + [m for m in GEMINI_FALLBACK_MODELS if m != model_id]
    prompt = """Extraia do texto abaixo os dados do pedido. Responda APENAS com um JSON válido, sem markdown.
Para cada item: use "unit": "par" para calçados (tênis, chinelo, sandália, bota) ou "unit": "unidade" para bolas, mochilas, bolsas, bonés, etc.
Se houver grade/tamanhos no texto (ex: 35: 2, 36: 4, 37: 3), inclua em "sizes": {"35": 2, "36": 4, "37": 3}.
Formato:
{"brand": "marca", "order_ref": "número", "delivery_date": "YYYY-MM-DD ou vazio", "items": [{"ref": "ref", "name": "descrição", "color": "cor", "qty": total, "unit": "par" ou "unidade", "sizes": {"35": 2, "36": 4} ou {}}], "confidence": 0.0 a 1.0}

Texto:
"""
    last_error = None
    for mid in models_to_try:
        try:
            model = genai.GenerativeModel(mid)
            response = model.generate_content(prompt + text[:30000])
            raw = (response.text or "").strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            if "confidence" not in data:
                data["confidence"] = 0.8
            data = _normalize_gemini_response(data)
            return data
        except Exception as e:
            last_error = e
            try_fallback = (
                mid != models_to_try[-1]
                and (_is_model_not_found_error(e) or _is_quota_error(e))
            )
            if try_fallback:
                msg = "429 quota exceeded" if _is_quota_error(e) else str(e)
                logger.warning("Gemini model %s failed (%s), trying fallback", mid, msg)
                continue
            err_msg = "429 quota exceeded" if _is_quota_error(e) else str(e)
            logger.warning("Gemini parse failed [%s]: %s", mid, err_msg)
            return {"confidence": 0.0, "error": err_msg if _is_quota_error(e) else str(e)}
    err_msg = "Gemini quota exceeded. Try again later or check billing: https://ai.google.dev/gemini-api/docs/rate-limits"
    if last_error and not _is_quota_error(last_error):
        err_msg = str(last_error)
    logger.warning("Gemini failed all models: %s", err_msg)
    return {"confidence": 0.0, "error": err_msg}


def extract_order_from_pdf(
    pdf_bytes: bytes,
    gemini_api_key: Optional[str] = None,
    confidence_threshold: float = 0.75,
) -> Dict[str, Any]:
    """
    Send the PDF directly to Gemini (vision/document) so it can read text, tables, images.
    Use when text extraction with PyMuPDF failed or returned nothing.
    Returns same shape as extract_order_from_text.
    """
    key = (gemini_api_key or "").strip()
    if not key:
        return {"confidence": 0.0, "error": "No GEMINI_API_KEY"}

    import tempfile
    import google.generativeai as genai
    genai.configure(api_key=key)
    raw_id = (os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    model_id = DEFAULT_GEMINI_MODEL if raw_id in _DEPRECATED_GEMINI_MODELS else raw_id
    models_to_try = [model_id] + [m for m in GEMINI_FALLBACK_MODELS if m != model_id]
    prompt = """Extraia do documento (PDF) os dados do pedido: marca, número, data de entrega e itens.
Para cada item: "unit": "par" para calçados (tênis, chinelo, sandália, bota) ou "unit": "unidade" para bolas, mochilas, bolsas, bonés.
Se houver grade/tamanhos (ex: 35, 36, 37 com quantidades), inclua em "sizes": {"35": 2, "36": 4}.
Responda APENAS com JSON válido, sem markdown:
{"brand": "marca", "order_ref": "número", "delivery_date": "YYYY-MM-DD ou vazio", "items": [{"ref": "ref", "name": "descrição", "color": "cor", "qty": total, "unit": "par" ou "unidade", "sizes": {"35": 2} ou {}}], "confidence": 0.0 a 1.0}
"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        uploaded = genai.upload_file(tmp_path, mime_type="application/pdf")
        last_error = None
        for mid in models_to_try:
            try:
                model = genai.GenerativeModel(mid)
                response = model.generate_content([uploaded, prompt])
                raw = (response.text or "").strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw)
                if "confidence" not in data:
                    data["confidence"] = 0.85
                data = _normalize_gemini_response(data)
                return data
            except Exception as e:
                last_error = e
                try_fallback = (
                    mid != models_to_try[-1]
                    and (_is_model_not_found_error(e) or _is_quota_error(e))
                )
                if try_fallback:
                    msg = "429 quota exceeded" if _is_quota_error(e) else str(e)
                    logger.warning("Gemini PDF model %s failed (%s), trying fallback", mid, msg)
                    continue
                err_msg = "429 quota exceeded" if _is_quota_error(e) else str(e)
                logger.warning("Gemini PDF extraction failed [%s]: %s", mid, err_msg)
                return {"confidence": 0.0, "error": err_msg if _is_quota_error(e) else str(e), "items": []}
        err_msg = "Gemini quota exceeded. Try again later or check billing: https://ai.google.dev/gemini-api/docs/rate-limits"
        if last_error and not _is_quota_error(last_error):
            err_msg = str(last_error)
        return {"confidence": 0.0, "error": err_msg, "items": []}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _extract_with_claude(text: str, api_key: str) -> Dict[str, Any]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = """Extraia do texto os dados do pedido. Responda APENAS com um JSON válido:
{"brand": "marca", "order_ref": "número pedido", "delivery_date": "YYYY-MM-DD ou vazio", "items": [{"ref": "...", "name": "...", "color": "...", "qty": N}], "confidence": 0.0 a 1.0}

Texto:
""" + text[:25000]
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text if msg.content else ""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        if "confidence" not in data:
            data["confidence"] = 0.85
        return data
    except Exception as e:
        logger.warning("Claude parse failed: %s", e)
        return {"confidence": 0.0, "error": str(e)}
