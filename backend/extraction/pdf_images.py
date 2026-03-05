# extraction/pdf_images.py - Extract images from PDFs using PyMuPDF
import base64
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Fraction of page height to treat as "top" (brand logos, headers). Images in this zone are skipped.
SKIP_TOP_FRACTION = 0.25

# Min dimension (px) to consider; smaller = likely logo/icon
MIN_PRODUCT_DIM = 100


def _size_bucket(w: int, h: int) -> tuple:
    """Bucket (w,h) so similar sizes group together. Returns (bucket_w, bucket_h)."""
    if w <= 0 or h <= 0:
        return (0, 0)
    # Normalize to a canonical size (smaller dimension = 100)
    scale = 100 / min(w, h)
    bw = int(w * scale)
    bh = int(h * scale)
    return (bw, bh)


def extract_images_from_pdf(
    pdf_content: bytes,
    skip_top_fraction: float = SKIP_TOP_FRACTION,
) -> List[dict]:
    """Extract embedded images from a PDF. Returns list of dicts with page, index, image_bytes, width, height, bbox.
    Skips images in the top portion of each page (typically brand logos)."""
    try:
        import fitz
    except ImportError:
        logger.warning("PyMuPDF not installed; pip install pymupdf")
        return []

    out = []
    seen_xrefs = set()
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_height = page.rect.height
            top_cutoff = page_height * skip_top_fraction

            try:
                infos = page.get_image_info(xrefs=True)
            except Exception:
                infos = []

            if not infos:
                for img_index, img in enumerate(page.get_images()):
                    xref = img[0]
                    if xref in seen_xrefs:
                        continue
                    try:
                        base = doc.extract_image(xref)
                        if base:
                            seen_xrefs.add(xref)
                            out.append({
                                "page": page_num + 1,
                                "index": len(out),
                                "image_bytes": base["image"],
                                "width": base.get("width", 0),
                                "height": base.get("height", 0),
                                "ext": base.get("ext", "png"),
                                "bbox": None,
                            })
                    except Exception:
                        pass
                continue

            infos_sorted = sorted(infos, key=lambda i: (i.get("bbox", (0, 0, 0, 0))[1], i.get("bbox", (0, 0, 0, 0))[0]))
            for img_index, info in enumerate(infos_sorted):
                bbox = info.get("bbox")
                if not bbox or len(bbox) < 4:
                    continue
                y0 = bbox[1]
                if y0 < top_cutoff:
                    continue
                xref = info.get("xref", 0)
                if not xref or xref in seen_xrefs:
                    continue
                try:
                    base = doc.extract_image(xref)
                    if base:
                        seen_xrefs.add(xref)
                        out.append({
                            "page": page_num + 1,
                            "index": len(out),
                            "image_bytes": base["image"],
                            "width": base.get("width", 0),
                            "height": base.get("height", 0),
                            "ext": base.get("ext", "png"),
                            "bbox": bbox,
                        })
                except Exception:
                    pass
        doc.close()
    except Exception as e:
        logger.warning("PDF image extraction failed: %s", e)
    return out


def _select_product_images(
    raw: List[dict],
    expected_count: Optional[int] = None,
    skip_top_fraction: float = SKIP_TOP_FRACTION,
    min_dim: int = MIN_PRODUCT_DIM,
) -> List[dict]:
    """
    From raw extracted images, select the ones likely to be product images.
    - Discard small images (min dimension < min_dim) - logos/icons
    - Discard singleton size groups (1 image of that size) - likely brand
    - Discard images in top fraction of page
    - Prefer the size cluster with count ~= expected_count (medium product images)
    """
    if not raw:
        return []

    # Filter: must have valid size (extract_images_from_pdf already excludes top-zone)
    candidates = []
    for r in raw:
        w, h = r.get("width", 0), r.get("height", 0)
        if w <= 0 or h <= 0:
            continue
        if min(w, h) < min_dim:
            continue  # Skip small (logos)
        candidates.append(r)

    if not candidates:
        return raw  # Fallback: return all that passed min_dim

    # Group by size bucket
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in candidates:
        bw, bh = _size_bucket(r["width"], r["height"])
        buckets[(bw, bh)].append(r)

    # Sort buckets by count descending; prefer bucket with count ~= expected_count
    sorted_buckets = sorted(buckets.items(), key=lambda x: -len(x[1]))

    # Discard singleton buckets (1 image of that size = likely brand)
    multi_buckets = [(k, v) for k, v in sorted_buckets if len(v) > 1]

    if not multi_buckets:
        # All singletons - return all candidates sorted by position, excluding smallest (likely logos)
        if candidates:
            # Sort by position, take up to expected_count, preferring larger images
            by_pos = sorted(candidates, key=lambda r: (r.get("page", 0), r.get("bbox", (0, 0, 0, 0))[1], r.get("bbox", (0, 0, 0, 0))[0]))
            # Exclude smallest 20% (likely logos)
            by_area = sorted(by_pos, key=lambda r: -(r.get("width", 0) * r.get("height", 0)))
            keep = max(1, int(len(by_area) * 0.8))
            selected = by_area[:keep]
            selected = sorted(selected, key=lambda r: (r.get("page", 0), r.get("bbox", (0, 0, 0, 0))[1], r.get("bbox", (0, 0, 0, 0))[0]))
            if expected_count:
                selected = selected[:expected_count]
            return selected
        return candidates

    # Prefer bucket with count closest to expected_count
    if expected_count and expected_count > 0:
        best_bucket = min(multi_buckets, key=lambda x: abs(len(x[1]) - expected_count))
    else:
        best_bucket = multi_buckets[0]  # Largest count

    selected = best_bucket[1]
    # Sort by position (page, y, x)
    selected = sorted(selected, key=lambda r: (r.get("page", 0), r.get("bbox", (0, 0, 0, 0))[1], r.get("bbox", (0, 0, 0, 0))[0]))

    if expected_count and len(selected) > expected_count:
        selected = selected[:expected_count]

    return selected


def pdf_to_images_as_base64(
    pdf_content: bytes,
    max_images: int = 50,
    min_size: int = MIN_PRODUCT_DIM,
    skip_top_fraction: float = SKIP_TOP_FRACTION,
    expected_count: Optional[int] = None,
) -> List[dict]:
    """
    Return list of { page, index, width, height, data_url } for frontend.
    Uses smarter filtering:
    - Loads all images, analyzes size distribution
    - Discards small (logos), singleton sizes (brand), top-zone images
    - Keeps medium cluster matching expected product count
    """
    raw = extract_images_from_pdf(pdf_content, skip_top_fraction=skip_top_fraction)
    selected = _select_product_images(raw, expected_count=expected_count, skip_top_fraction=skip_top_fraction, min_dim=min_size)

    result = []
    for r in selected:
        b = r.get("image_bytes")
        if not b:
            continue
        w, h = r.get("width", 0), r.get("height", 0)
        if min(w, h) < min_size:
            continue
        if len(result) >= max_images:
            break
        ext = (r.get("ext") or "png").lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
        data_url = f"data:{mime};base64," + base64.b64encode(b).decode()
        result.append({
            "page": r["page"],
            "index": len(result),
            "width": w,
            "height": h,
            "data_url": data_url,
        })
    return result
