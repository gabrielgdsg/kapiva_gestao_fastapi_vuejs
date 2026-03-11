from fastapi import APIRouter, HTTPException, Response, File, UploadFile, Query, Path
from fastapi.responses import FileResponse
from .levantamentos_postgres import LevantamentoPostgres
from ..models.levantamentos import LevantamentoEstoque, MarcaFornecedor, Marcas, Fornecedor, Produto, ProdutoIdentifier, ProdutoImageSave
from db_mongo.database import engine, db
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
import base64
import requests
from typing import List, Optional
from functools import lru_cache
import time

router = APIRouter()
import logging

logger = logging.getLogger(__name__)

# PERFORMANCE: In-memory cache for levantamentos queries (5-minute TTL)
# Key: (date_ini, date_fim, cod_marca, timestamp_bucket)
# This makes repeated queries near-instant (<50ms)
@lru_cache(maxsize=100)
def _cached_levantamentos_query(date_ini: str, date_fim: str, cod_marca: str, time_bucket: int):
    """
    Cached wrapper for database query.
    time_bucket changes every 5 minutes, invalidating cache.
    """
    return LevantamentoPostgres.load_estoque_from_db(date_ini, date_fim, cod_marca)


# @router.get("/api/levantamentos/{data_cadastro_ini}/{data_cadastro_fim}/{cod_marca}")
# async def read_levantamentos(data_cadastro_ini: str, data_cadastro_fim: str, cod_marca: str):
#     data_cadastro_ini_datetime = datetime.fromisoformat(data_cadastro_ini)
#     data_cadastro_fim_datetime = datetime.fromisoformat(data_cadastro_fim)
#
#     levantamento_loaded = LevantamentoPostgres.load_estoque_from_db(data_cadastro_ini, data_cadastro_fim, cod_marca)
#     levantamento_estoque_list = []
#     for i in range(len(levantamento_loaded)):
#         print(levantamento_loaded[i][5], levantamento_loaded[i][6],levantamento_loaded[i][7])
#         levantamento_estoque = LevantamentoEstoque(
#             cod_grupo=levantamento_loaded[i][0], des_grupo=levantamento_loaded[i][1],
#             cod_subgrupo=levantamento_loaded[i][2], des_subgrupo=levantamento_loaded[i][3],
#             cod_produto=levantamento_loaded[i][4], des_produto=levantamento_loaded[i][5],
#             cod_barra=levantamento_loaded[i][6], cod_referencia=levantamento_loaded[i][7],
#             qtd=levantamento_loaded[i][8], saldo_estoque=levantamento_loaded[i][9],
#             vlr_custo_bruto=levantamento_loaded[i][10], vlr_custo_aquis=levantamento_loaded[i][11],
#             vlr_venda1=levantamento_loaded[i][12], total=levantamento_loaded[i][13],
#             cod_grade=levantamento_loaded[i][14], des_grade=levantamento_loaded[i][15],
#             cod_tamanho=levantamento_loaded[i][16], des_tamanho=levantamento_loaded[i][17],
#             cod_cor=levantamento_loaded[i][18], des_cor=levantamento_loaded[i][19],
#             dat_cadastro=levantamento_loaded[i][20], dat_alteracao=levantamento_loaded[i][21],
#             dat_emissao=levantamento_loaded[i][22], dat_lancamento=levantamento_loaded[i][23],
#             dat_saida=levantamento_loaded[i][24], cod_fornecedor=levantamento_loaded[i][25],
#             raz_fornecedor=levantamento_loaded[i][26], fan_fornecedor=levantamento_loaded[i][27],
#             cod_marca=levantamento_loaded[i][28], nom_marca=levantamento_loaded[i][29],
#             tipo_movto=levantamento_loaded[i][30], qtd_movto=levantamento_loaded[i][31], data_movto=levantamento_loaded[i][32],
#             cod_movto=levantamento_loaded[i][33], cod_origem_movto=levantamento_loaded[i][34]
#         )
#         levantamento_estoque_list.append(levantamento_estoque)
#
#     return jsonable_encoder(levantamento_estoque_list)


@router.get("/api/levantamentos/{data_cadastro_ini}/{data_cadastro_fim}/{cod_marca}")
async def read_levantamentos(
    data_cadastro_ini: str,
    data_cadastro_fim: str,
    cod_marca: str,
    source: Optional[str] = Query(None, description="Use 'mongo' to prefer MongoDB cache (faster for large brands)"),
):
    """
    PERFORMANCE OPTIMIZED:
    1. If source=mongo: try MongoDB first (fast), fallback to PostgreSQL
    2. In-memory cache for 5 minutes (repeated queries <50ms)
    3. Formats dates on backend (eliminates 800+ moment.js operations)
    """
    start_time = time.time()

    # Try MongoDB first when source=mongo
    if source and source.lower() == "mongo":
        from .levantamentos_sync import get_from_mongo
        mongo_data = await get_from_mongo(data_cadastro_ini, data_cadastro_fim, cod_marca)
        if mongo_data is not None:
            execution_time = time.time() - start_time
            print(f"[PERFORMANCE] Levantamentos query: {execution_time*1000:.0f}ms | {len(mongo_data)} rows | MONGO")
            return jsonable_encoder(mongo_data)

    # Fallback to PostgreSQL
    current_time = int(time.time())
    time_bucket = current_time // 300
    levantamento_loaded = _cached_levantamentos_query(
        data_cadastro_ini, data_cadastro_fim, cod_marca, time_bucket
    )

    formatted_data = []
    for row in levantamento_loaded:
        row_list = list(row)
        if row_list[20]:
            if hasattr(row_list[20], 'strftime'):
                row_list[20] = row_list[20].strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif not isinstance(row_list[20], str):
                row_list[20] = str(row_list[20])
        else:
            row_list[20] = '1900-01-01T00:00:00.000000'
        if row_list[21]:
            if hasattr(row_list[21], 'strftime'):
                row_list[21] = row_list[21].strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif not isinstance(row_list[21], str):
                row_list[21] = str(row_list[21])
        else:
            row_list[21] = '1900-01-01T00:00:00.000000'
        if len(row_list) > 29 and row_list[29]:
            if hasattr(row_list[29], 'strftime'):
                row_list[29] = row_list[29].strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif not isinstance(row_list[29], str):
                row_list[29] = str(row_list[29])
        formatted_data.append(row_list)

    execution_time = time.time() - start_time
    cache_info = _cached_levantamentos_query.cache_info()
    cache_status = "CACHED" if cache_info.hits > 0 else "FRESH"
    print(f"[PERFORMANCE] Levantamentos query: {execution_time*1000:.0f}ms | {len(formatted_data)} rows | {cache_status} | Cache: {cache_info.hits}/{cache_info.hits + cache_info.misses}")
    return jsonable_encoder(formatted_data)


@router.post("/api/levantamentos/sync")
async def force_sync_levantamentos(
    data_ini: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="Data final (YYYY-MM-DD)"),
    cod_marca: str = Query(..., description="Código da marca"),
):
    """
    Force sync levantamentos from PostgreSQL to MongoDB.
    Use after loading to populate cache for faster subsequent loads.
    """
    from .levantamentos_sync import sync_levantamentos
    result = await sync_levantamentos(data_ini, data_fim, cod_marca)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Sync failed"))
    return result


@router.post("/api/levantamentos/sync-all")
async def sync_all_marcas(
    data_ini: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="Data final (YYYY-MM-DD)"),
):
    """
    Sync all marcas from PostgreSQL to MongoDB for the given date range.
    Intended for daily cron: POST /api/levantamentos/sync-all?data_ini=2024-01-01&data_fim=2026-12-31
    """
    from .levantamentos_sync import sync_levantamentos
    marcas = LevantamentoPostgres.load_marcas_from_db()
    if not marcas:
        return {"ok": True, "synced": 0, "message": "No marcas found"}
    results = []
    for m in marcas:
        cod = str(m.get("cod_marca", ""))
        if not cod:
            continue
        r = await sync_levantamentos(data_ini, data_fim, cod)
        results.append({"cod_marca": cod, "nom_marca": m.get("nom_marca", ""), **r})
    ok_count = sum(1 for r in results if r.get("ok"))
    return {"ok": True, "synced": ok_count, "total_marcas": len(marcas), "results": results}


@router.get("/api/movimento/{cod_produto}")
async def read_movimento(cod_produto: int):
    """
    PERFORMANCE: Load movimento data on-demand for specific product.
    Called when user expands product row. Much faster than loading all movimento upfront!
    """
    start_time = time.time()
    
    movimento_data = LevantamentoPostgres.load_movimento_by_produto(cod_produto)
    
    # Format dates
    formatted_movimento = []
    for row in movimento_data:
        row_list = list(row)
        
        # Format data_movto (index 2)
        if row_list[2]:
            if hasattr(row_list[2], 'strftime'):
                row_list[2] = row_list[2].strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif not isinstance(row_list[2], str):
                row_list[2] = str(row_list[2])
        
        formatted_movimento.append({
            'tipo_movto': row_list[0],
            'qtd_movto': row_list[1],
            'data_movto': row_list[2],
            'cod_movto': row_list[3],
            'cod_origem_movto': row_list[4],
            'cod_produto': row_list[5]
        })
    
    execution_time = time.time() - start_time
    print(f"[PERFORMANCE] Movimento query for produto {cod_produto}: {execution_time*1000:.0f}ms | {len(formatted_movimento)} rows")
    
    return jsonable_encoder(formatted_movimento)


@router.get("/api/debug/reload-version")
async def debug_reload_version():
    """Returns a version string to verify backend deploy. Should be 'reload-v2' after fix."""
    return {"version": "reload-v2", "method": "load_marcas_from_db"}


@router.get("/api/debug/mongodb-images")
async def debug_mongodb_images():
    """
    Diagnostic: check if product images exist in MongoDB.
    Use after deploy/rebuild to verify mongo_data volume was preserved.
    Returns: collection counts, Produto docs with/without img, sample brands.
    """
    out = {"mongo_ok": False, "collections": [], "produto": {}, "produtoestoque": {}, "hint": ""}
    try:
        # List collections
        coll_names = await db.list_collection_names()
        out["collections"] = coll_names
        out["mongo_ok"] = True

        # Produto (levantamentos - product images for Levantamentos view)
        prod_coll = engine.get_collection(Produto)
        total = await prod_coll.count_documents({})
        with_img = await prod_coll.count_documents({"img": {"$exists": True, "$nin": [None, ""]}})
        # Sample brands that have images
        pipeline = [
            {"$match": {"img": {"$exists": True, "$nin": [None, ""]}}},
            {"$group": {"_id": "$nom_marca", "count": {"$sum": 1}}},
            {"$limit": 5},
        ]
        brands_with_img = []
        async for doc in prod_coll.aggregate(pipeline):
            brands_with_img.append({"marca": doc["_id"], "count": doc["count"]})

        out["produto"] = {
            "total": total,
            "with_img": with_img,
            "without_img": total - with_img,
            "sample_brands_with_img": brands_with_img,
        }

        # ProdutoEstoqueMongoBeanie (estoque - Beanie uses class name as collection)
        for cname in coll_names:
            if "produto" in cname.lower() and "estoque" in cname.lower():
                try:
                    c = db[cname]
                    out["produtoestoque"] = {
                        "collection": cname,
                        "total": await c.count_documents({}),
                        "with_img": await c.count_documents({"img": {"$exists": True, "$nin": [None, ""]}}),
                    }
                    break
                except Exception as e:
                    out["produtoestoque"] = {"collection": cname, "error": str(e)}
        if "produtoestoque" not in out:
            out["produtoestoque"] = {"note": "no produtoestoque collection found"}

        if total == 0:
            out["hint"] = "Produto collection is empty. Data may have been lost (volume removed?) or never synced. Check: docker volume ls | grep mongo"
        elif with_img == 0:
            out["hint"] = "Produto docs exist but none have img. Images were never saved or were cleared. You may need to re-paste/save images per product."
        else:
            out["hint"] = "Images exist. If UI shows none, check frontend API calls or filters."
    except Exception as e:
        out["error"] = str(e)
        out["hint"] = "MongoDB unreachable. Is mongo container running? docker ps | grep mongo"
    return out


@router.get("/api/reloadfrompostgresdb/marcafornecedor/")
async def reloadfrompostgresdb_marcafornecedor():
    """Reload marcas from PostgreSQL into MongoDB. Uses load_marcas_from_db (simple, reliable)."""
    steps = []
    try:
        # Step 1: drop MongoDB collection
        try:
            marcas_collection = engine.get_collection(Marcas)
            marcas_collection.drop()
            steps.append("mongo_drop:ok")
        except Exception as e1:
            steps.append(f"mongo_drop:fail:{e1!s}")
            raise

        # Step 2: load from PostgreSQL
        try:
            marcas_list = LevantamentoPostgres.load_marcas_from_db()
            steps.append(f"postgres_load:ok:{len(marcas_list or [])} rows")
        except Exception as e2:
            steps.append(f"postgres_load:fail:{e2!s}")
            raise

        if not marcas_list:
            return []

        # Step 3: save to MongoDB
        try:
            marcas_to_save = [Marcas(cod_marca=m["cod_marca"], nom_marca=m["nom_marca"], fornecedores=[]) for m in marcas_list]
            await engine.save_all(marcas_to_save)
            steps.append(f"mongo_save:ok:{len(marcas_to_save)}")
        except Exception as e3:
            steps.append(f"mongo_save:fail:{e3!s}")
            raise

        return jsonable_encoder(marcas_to_save)
    except Exception as e:
        logger.exception("reloadfrompostgresdb_marcafornecedor failed: %s", e)
        raise HTTPException(status_code=500, detail=f"steps={steps} error={e!s}")


# @router.get("/api/read/marcafornecedor/")
# async def read_marcafornecedor():
#     marcas_fornecedores_obj = await engine.find(MarcaFornecedor)
#     return jsonable_encoder(marcas_fornecedores_obj)


@router.get("/api/read/marcas/debug")
async def read_marcas_debug():
    """Diagnostic: check MongoDB count, PostgreSQL fallback, and Postgres connectivity."""
    mongo_count = 0
    mongo_err = None
    try:
        marcas_obj = await engine.find(Marcas)
        mongo_count = len(marcas_obj) if marcas_obj else 0
    except Exception as e:
        mongo_err = str(e)
    pg_count = 0
    pg_err = None
    try:
        marcas_list = LevantamentoPostgres.load_marcas_from_db()
        pg_count = len(marcas_list) if marcas_list else 0
    except Exception as e:
        pg_err = str(e)
    return {
        "mongo_count": mongo_count,
        "mongo_error": mongo_err,
        "postgres_fallback_count": pg_count,
        "postgres_error": pg_err,
        "effective_source": "mongo" if mongo_count > 0 else ("postgres" if pg_count > 0 else "none"),
    }


@router.get("/api/read/marcas/")
async def read_marcas():
    """Return marcas from MongoDB. If empty (e.g. fresh DB), fallback to PostgreSQL."""
    try:
        marcas_obj = await engine.find(Marcas)
    except Exception as e:
        logger.warning("read_marcas: MongoDB find failed: %s", e)
        marcas_obj = []
    if marcas_obj:
        return jsonable_encoder(marcas_obj)
    logger.info("read_marcas: MongoDB empty, trying PostgreSQL fallback")
    try:
        marcas_list = LevantamentoPostgres.load_marcas_from_db()
        logger.info("read_marcas: fallback returned %d marcas", len(marcas_list))
        return marcas_list
    except Exception as e:
        logger.warning("read_marcas: PostgreSQL fallback failed: %s", e)
        return []


# def get_as_base64(image_url):
#     return base64.b64encode(requests.get(image_url).content)


@router.get("/api/fetch/produtos/")
async def insert_image():
    with open("nike.png", "rb") as img_file:
        base64_encoded_data = base64.b64encode(img_file.read())

    # with open(request.GET["nike.jpg"], "rb") as image_file:
    #     encoded_string = base64.b64encode(image_file.read())
    # with open("nike.jpg", "rb") as image_file:
    #     encoded_string = base64.b64encode(image_file.read())
    url = 'https://cdnv2.moovin.com.br/awallon/imagens/produtos/original/tenis-indoor-nike-beco-2-646433-006-pretocinza-d08805a4eb85e50a4092cd4474284a95.jpg'
    encoded_string = base64.b64encode(requests.get(url).content)
    print(encoded_string)
    # produto = Produto(cod_referencia='646433', nom_marca='nike', des_cor='preto', img=encoded_string)
    produto = Produto(cod_referencia='646433', nom_marca='nike', des_cor='preto', img=base64_encoded_data)
    await engine.save(produto)
    # abc=db.database_name.insert({"image":encoded_string})
    # abc=db.database_name.insert({"image":encoded_string})
    # decode = produto.img.decode()
    # img_tag = '<img alt="sample" src="data:image/png;base64,{0}">'.format(decode)
    return produto


# @router.put("/api/produtos/images/")
# # @router.put("/api/produtos/images/{nom_marca}")
# # async def insert_image(produto: Produto):
# async def insert_images(produtos: List[Produto]):
#     for produto in produtos:
#         db_produto = await engine.find_one(Produto,
#                                            Produto.cod_referencia == produto.cod_referencia and
#                                            Produto.nom_marca == produto.nom_marca and
#                                            Produto.des_cor == produto.des_cor)
#         if db_produto is None:
#             base64_encoded_data = base64.b64encode(requests.get(produto.img).content)
#             new_produto = Produto(cod_referencia=produto.cod_referencia, nom_marca=produto.nom_marca,
#                                   des_cor=produto.des_cor, img=base64_encoded_data)
#             await engine.save(new_produto)
#     return


@router.put("/api/produtos/image")
async def save_produto_image(payload: ProdutoImageSave):
    """
    Save a single product image (from paste or URL). Finds by (cod_referencia, nom_marca, des_cor)
    and updates img. Creates new document if not found (with minimal fields).
    """
    ref = (payload.cod_referencia or "").strip()
    marca = (payload.nom_marca or "").strip()
    cor = (payload.des_cor or "").strip() or "padrao"
    des_produto = (payload.des_produto or "").strip()
    if not ref or not marca:
        raise HTTPException(status_code=400, detail="cod_referencia and nom_marca required")
    db_produto = await engine.find_one(
        Produto,
        Produto.cod_referencia == ref,
        Produto.nom_marca == marca,
        Produto.des_cor == cor,
    )
    if db_produto is not None:
        db_produto.img = payload.img
        await engine.save(db_produto)
        return {"status": "updated", "cod_referencia": ref, "des_cor": cor}
    # Create new - need minimal Produto. Use defaults for required fields.
    from bson import Decimal128
    new_produto = Produto(
        cod_grupo=0, des_grupo="", cod_subgrupo=0, des_subgrupo="",
        cod_produto=0, des_produto=des_produto or ref,
        vlr_custo_bruto=Decimal128("0"), vlr_custo_aquis=Decimal128("0"), vlr_venda1=Decimal128("0"),
        cod_grade=0, des_grade="", cod_cor=0,
        dat_cadastro=datetime(1900, 1, 1), dat_ultcompra=datetime(1900, 1, 1),
        cod_fornecedor=0, raz_fornecedor="", fan_fornecedor="",
        cod_marca=0, cod_referencia=ref, nom_marca=marca, des_cor=cor,
        img=payload.img
    )
    await engine.save(new_produto)
    return {"status": "created", "cod_referencia": ref, "des_cor": cor}


@router.put("/api/produtos/save")
async def save_produtos(produtos: List[Produto]):
    saved_count = 0
    created_count = 0
    
    for produto in produtos:
        try:
            # Find existing product in MongoDB
            db_produto = await engine.find_one(
                Produto,
                Produto.cod_referencia == produto.cod_referencia,
                Produto.nom_marca == produto.nom_marca,
                Produto.des_cor == produto.des_cor,
                Produto.des_produto == produto.des_produto
            )
            
            if db_produto is not None:
                # Update existing product
                print(f'[SAVE] Updating existing product: {produto.cod_referencia} - {produto.des_cor}')
                db_produto.img = produto.img
                await engine.save(db_produto)
                saved_count += 1
            else:
                # Create new product
                print(f'[SAVE] Creating new product: {produto.cod_referencia} - {produto.des_cor}')
                await engine.save(produto)
                created_count += 1
                
        except Exception as e:
            print(f'[ERROR] Failed to save product {produto.cod_referencia}: {str(e)}')
            continue
    
    print(f'[SAVE] Summary: {saved_count} updated, {created_count} created')
    return {"status": "success", "updated": saved_count, "created": created_count}


# @router.post("/api/produtos/images/")
# async def read_produtos(produtos: List[Produto]):
# # async def get_produtos(produtos: Optional[List[Produto]] = Query(None)):
#     db_produto_list = []
#     for produto in produtos:
#         db_produto = await engine.find_one(Produto,
#                                            Produto.cod_referencia == produto.cod_referencia and
#                                            Produto.nom_marca == produto.nom_marca and
#                                            Produto.des_cor == produto.des_cor)
#         if db_produto is not None:
#             db_produto_list.append(db_produto)
#         else:
#             return
#     return jsonable_encoder(db_produto_list)


def _img_fingerprint(img: Optional[str]) -> str:
    """Short fingerprint to detect if two images are the same (for diagnostics)."""
    if not img or not isinstance(img, str):
        return "empty"
    s = img[:400] if len(img) > 400 else img
    return str(hash(s))


def _normalize(s: Optional[str]) -> str:
    """Normalize for comparison: strip and collapse internal spaces."""
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.split())


def _normalize_color(s: Optional[str]) -> str:
    """Normalize color: strip, collapse spaces, slash to space for matching."""
    if not s or not isinstance(s, str):
        return ""
    return " ".join(str(s).replace("/", " ").split())


@router.put("/api/produtos/images/")
async def read_produtos(produtos: List[ProdutoIdentifier]):
    """
    Load images from MongoDB for a list of products.
    Uses simplified ProdutoIdentifier model to avoid strict validation issues.
    Tries exact match first; then fallback by (cod_referencia, nom_marca, des_cor) with normalized des_produto.
    Returns REQUEST identifiers (cod_referencia, des_cor) so frontend keys match.
    """
    import re
    produto_list = []
    coll = engine.get_collection(Produto)
    for produto in produtos:
        ref = (produto.cod_referencia or "").strip()
        marca = (produto.nom_marca or "").strip()
        cor = (produto.des_cor or "").strip() or "—"
        want_norm = _normalize(produto.des_produto)
        want_cor_norm = _normalize_color(cor)

        db_produto = None
        # 1. Exact match
        db_produto = await engine.find_one(Produto,
                                           Produto.cod_referencia == ref,
                                           Produto.nom_marca == marca,
                                           Produto.des_cor == cor,
                                           Produto.des_produto == produto.des_produto)
        if db_produto is None:
            # 2. (ref, marca, cor) with normalized des_produto
            cursor = engine.find(
                Produto,
                Produto.cod_referencia == ref,
                Produto.nom_marca == marca,
                Produto.des_cor == cor,
            )
            first_by_ref_marca_cor = None
            async for candidate in cursor:
                if first_by_ref_marca_cor is None:
                    first_by_ref_marca_cor = candidate
                if want_norm and _normalize(getattr(candidate, "des_produto", "") or "") == want_norm:
                    db_produto = candidate
                    break
            if db_produto is None:
                db_produto = first_by_ref_marca_cor
        if db_produto is None and ref:
            # 3. cod_referencia prefix (e.g. "44600112561" matches "44600112561-17")
            pattern = "^" + re.escape(ref) + r"($|[-.])"
            first_with_img = None
            async for doc in coll.find({"cod_referencia": {"$regex": pattern}}):
                img_val = doc.get("img")
                if not img_val:
                    continue
                db_marca = (doc.get("nom_marca") or "").upper()
                db_cor_norm = _normalize_color(doc.get("des_cor") or "")
                if first_with_img is None:
                    first_with_img = img_val
                if (not marca or db_marca == marca.upper()) and (not want_cor_norm or db_cor_norm == want_cor_norm):
                    db_produto = type("_Img", (), {"img": img_val})()
                    break
            if db_produto is None and first_with_img:
                db_produto = type("_Img", (), {"img": first_with_img})()
        if db_produto is None and ref and marca.strip():
            # 4. ref + case-insensitive marca
            async for doc in coll.find({
                "cod_referencia": ref,
                "nom_marca": {"$regex": "^" + re.escape(marca) + "$", "$options": "i"}
            }):
                img_val = doc.get("img")
                if img_val:
                    db_produto = type("_Img", (), {"img": img_val})()
                    break
        if db_produto is not None:
            # Return REQUEST identifiers so frontend key matches
            produto_list.append({
                "cod_referencia": ref,
                "nom_marca": marca,
                "des_cor": cor,
                "des_produto": produto.des_produto,
                "img": db_produto.img,
            })

    # Diagnostics: log whether we're returning distinct images or the same one for all
    if produto_list:
        fingerprints = [_img_fingerprint(p.get("img")) for p in produto_list]
        unique_fp = len(set(fingerprints))
        logger.info(
            "Images API: requested=%d found=%d unique_img_fingerprints=%d (sample: %s)",
            len(produtos), len(produto_list), unique_fp,
            [produto_list[i].get("cod_referencia") + "/" + produto_list[i].get("des_cor", "") for i in range(min(3, len(produto_list)))]
        )
        if unique_fp == 1 and len(produto_list) > 1:
            logger.warning("Images API: all %d returned products have the SAME image (MongoDB likely has one placeholder for all).", len(produto_list))
    elif produtos:
        logger.info("Images API: requested=%d found=0 (no matching products in MongoDB)", len(produtos))

    return jsonable_encoder(produto_list)
    # return jsonable_encoder(db_produto)


@router.get("/api/produtos/images/debug")
async def debug_images_by_marca(nom_marca: str = "FERRACINI", limit: int = 30):
    """
    Inspect what images MongoDB has for a given brand.
    Returns metadata only (no base64): cod_referencia, des_cor, des_produto, img_length, img_fingerprint.
    If all img_fingerprint values are the same, the DB has one image reused for all products.
    """
    out = []
    cursor = engine.find(Produto, Produto.nom_marca == nom_marca)
    count = 0
    first_fp = None
    async for db_produto in cursor:
        if count >= limit:
            break
        img = getattr(db_produto, "img", None)
        fp = _img_fingerprint(img) if img else "empty"
        if first_fp is None:
            first_fp = fp
        out.append({
            "cod_referencia": getattr(db_produto, "cod_referencia", ""),
            "des_cor": getattr(db_produto, "des_cor", ""),
            "des_produto": (getattr(db_produto, "des_produto", "") or "")[:50],
            "img_length": len(img) if img else 0,
            "img_fingerprint": fp,
            "same_as_first": fp == first_fp,
        })
        count += 1
    return {"nom_marca": nom_marca, "count": len(out), "all_same_image": all(r["same_as_first"] for r in out) if out else None, "items": out}


# @router.post("/images/")
# async def create_upload_file(file: UploadFile = File(...)):
#
#     file.filename = "nike.jpg"
#     # file.filename = f"{uuid.uuid4()}.jpg"
#     contents = await file.read()  # <-- Important!
#
#     # db.append(contents)
#
#     return {"filename": file.filename}
#
#
# @router.get("/images/")
# async def read_random_file():
#     response = engine.find_one(Produto)
#     # response = Response(content=db[random_index])
#
#     return response

# def retrieve_image(request):
#     data = db.database_name.find()
#     data1 = json.loads(dumps(data))
#     img = data1[0]
#     img1 = img['image']
#     decode=img1.decode()
#     img_tag = '<img alt="sample" src="data:image/png;base64,{0}">'.format(decode)
#     return HttpResponse(img_tag)

# import base64
# import requests
# def get_as_base64(url):
#     return base64.b64encode(requests.get(url).content)

# import base64
# import requests
# @router.get("/api/testecosia/")
# async def test_ecosia():
#     image_url = 'https://cdnv2.moovin.com.br/awallon/imagens/produtos/original/tenis-indoor-nike-beco-2-646433-006-pretocinza-d08805a4eb85e50a4092cd4474284a95.jpg'
#
#     with open(image_url, "rb") as imageFile:
#         str = base64.b64encode(imageFile.read())
#         str in mongo
#
#     return base64.b64encode(requests.get(url).content)


# async def load_comissao_intervalo_from_db(data_ini_datetime: datetime, data_fim_datetime: datetime):
#     collection = engine.get_collection(ComissaoDia)
#     pipeline = [{'$match': {'data_comissao': {'$gte': data_ini_datetime, '$lte': data_fim_datetime}}},
#                 {'$unwind': {'path': '$comissao_vendedores'}},
#                 {'$group': {'_id': '$comissao_vendedores.cod_vendedor',
#                             'nom_vendedor': {'$first': '$comissao_vendedores.nom_vendedor'},
#                             'base_calc_comissao': {'$sum': '$comissao_vendedores.base_calc_comissao'},
#                             'cred_dev': {'$sum': '$comissao_vendedores.cred_dev'},
#                             'data_ini': {'$first': '$comissao_vendedores.data_ini'},
#                             'data_fim': {'$first': '$comissao_vendedores.data_fim'},
#                             'vlr_comissao': {'$sum': '$comissao_vendedores.vlr_comissao'},
#                             'comissao_total': {'$sum': '$comissao_total'}}},
#                 {'$sort': {'base_calc_comissao': -1}}]
#     documents0 = await collection.aggregate(pipeline).to_list(length=None)
#     comissao_total = documents0[0]['comissao_total'] or 0
#
#     pipeline.append(
#         {'$project': {'_id': 0, 'cod_vendedor': '$_id', 'nom_vendedor': '$nom_vendedor',
#                       'base_calc_comissao': '$base_calc_comissao', 'cred_dev': '$cred_dev', 'data_ini': '$data_ini',
#                       'data_fim': '$data_fim', 'vlr_comissao': '$vlr_comissao'}}
#     )
#     documents = await collection.aggregate(pipeline).to_list(length=None)
#     comissao_vendedores_list = [ComissaoVendedor.parse_doc(doc) for doc in documents]
#     comissao_intervalo = ComissaoDia(data_comissao=data_fim_datetime,
#                                      comissao_vendedores=comissao_vendedores_list, comissao_total=comissao_total)
#     return jsonable_encoder(comissao_intervalo)


# @router.get("/api/comissao/{data_ini}/{data_fim}")
# async def read_comissao(data_ini: str, data_fim: str):
#     data_fim_datetime = datetime.fromisoformat(data_fim)
#     comissao_dia = await engine.find_one(ComissaoDia, ComissaoDia.data_comissao == data_fim_datetime)
#     if comissao_dia is None:
#     # if data_ini == data_fim and comissao_dia is None:
#         comissao_loaded = ComissaoPostgres.load_comissao_from_db(data_ini, data_fim)
#         comissao_vendedores = []
#         sum_comissao = 0
#         for i in range(len(comissao_loaded)):
#             comissao_vendedor = ComissaoVendedor(cod_vendedor=comissao_loaded[i][0], nom_vendedor=comissao_loaded[i][1],
#                          base_calc_comissao=comissao_loaded[i][2],
#                          vlr_comissao=comissao_loaded[i][4],
#                          cred_dev=comissao_loaded[i][3], data_ini=datetime.fromisoformat(data_ini), data_fim=datetime.fromisoformat(data_fim))
#             comissao_vendedores.append(comissao_vendedor)
#             sum_comissao = sum_comissao + comissao_loaded[i][2]
#         comissao_dia = ComissaoDia(data_comissao=datetime.fromisoformat(data_fim), comissao_vendedores=comissao_vendedores, comissao_total=sum_comissao)
#         await engine.save(comissao_dia)
#     # else:
#     #     comissao_updated = ComissaoDia(**{**comissao_dia.dict(), "id": comissao_dia.id})
#     #     await engine.save(comissao_updated)
#     return jsonable_encoder(comissao_dia)


# @router.get("/api/comissaozaoo/{data_ini}/{data_fim}")
# async def gett_comissao():
#     return "test"

# async def update_comissao(caixa_put: Caixa):
#     caixa = await engine.find_one(Caixa, Caixa.data_caixa == caixa_put.data_caixa)
#     if caixa is not None:
#         # Creating a new instansce of caixa with 'id' from the existant one
#         caixa_updated = Caixa(**{**caixa_put.dict(), "id": caixa.id})
#         await engine.save(caixa_updated)
#     else:
#         await engine.save(caixa_put)
#     return "db_updated"

# async def update_comissao(data_ini: str, data_fim: str):
#     # ////////////start from here??
#
# @router.put("/api/comissao/add", response_model=ComissaoVendedor)
# async def add_comissao(comissao: ComissaoVendedor):
#     await engine.save(comissao)
#     print(comissao)
#     return comissao

# @api_comissao.route('/select', methods=['GET', 'POST'])
# def select():
#     nova_comissao = []
#     if request.method == 'POST':
#         Comissao.query.delete()  # clear comissao table first
#         data = request.get_json()
#         data_ini = datetime.strptime(data['data_ini'], '%Y-%m-%d').date()
#         data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
#         comissao_loaded = ComissaoPostgres.load_comissao_from_db(data_ini, data_fim)
#         # create list of rows, each of type Comissao
#         for i in range(len(comissao_loaded.cod_vendedor)):
#             nova_comissao.append(Comissao(cod_vendedor=comissao_loaded.cod_vendedor[i], nom_vendedor=comissao_loaded.nom_vendedor[i],
#                                           base_calc_comissao=comissao_loaded.base_calc_comissao[i], vlr_comissao=comissao_loaded.vlr_comissao[i],
#                                           cred_dev= comissao_loaded.cred_dev[i], dat_emissao_ini=data_ini, dat_emissao_fim=data_fim))
#         db.session.add_all(nova_comissao)
#         db.session.commit()
#         print([c.to_dict() for c in nova_comissao])
#         return jsonify([c.to_dict() for c in nova_comissao]), 201
#     elif request.method == 'GET':
#         nova_comissao = Comissao.query.all()
#         sum_comissao = 0
#         for item in nova_comissao:
#             sum_comissao = sum_comissao + item.base_calc_comissao
#         return jsonify([c.to_dict() for c in nova_comissao]), 201


@router.get("/api/levantamentos/performance/{ano_analise}")
async def get_selling_performance(ano_analise: int = Path(..., description="Year to analyze for performance metrics")):
    """
    Get selling performance metrics for all products grouped by reference+color.
    Returns performance scores (0-100) where higher = faster selling.
    """
    try:
        performance_data = LevantamentoPostgres.get_selling_performance(ano_analise)
        logger.info(f"Returning performance data for {len(performance_data)} products (year {ano_analise})")
        if len(performance_data) > 0:
            # Log sample for debugging
            sample_keys = list(performance_data.keys())[:3]
            for key in sample_keys:
                perf = performance_data[key]
                logger.info(f"Sample {key}: score={perf.get('score')}, velocity={perf.get('velocity')}, total_sold={perf.get('total_sold')}")
        return performance_data
    except Exception as e:
        logger.error(f"Error getting selling performance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
