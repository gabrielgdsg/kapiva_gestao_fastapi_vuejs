from fastapi import APIRouter, HTTPException, Query, Body
from .vendedor_postgres import VendedorPostgres
from ..models.vendedor import (
    VendedorMetas, MetaMensal, VendedorGrupo, 
    VendedorConfigMetas, VendedorTipo, VendedorSlug
)
from db_mongo.database import engine
from typing import Optional, List, Dict
from datetime import datetime, date
from bson import Decimal128
import logging
import math
import random
import re
import unicodedata
import calendar

logger = logging.getLogger(__name__)
router = APIRouter()

# MODULE LOAD VERIFICATION - This log will appear when module is loaded
logger.info("=" * 80)
logger.info("MODULE LOADED: api_vendedor.py - NEW VERSION WITH _calcular_metas_internal")
logger.info("=" * 80)


@router.get("/api/vendedor/version-check")
async def version_check():
    """Test endpoint to verify new code is running."""
    return {
        "version": "NEW_VERSION_2026_01_24",
        "has_calcular_metas_internal": "_calcular_metas_internal" in globals(),
        "message": "If you see this, the new code is loaded!"
    }


@router.get("/api/vendedor/debug-columns/{table}")
async def debug_table_columns(table: str):
    """Debug: show columns for a PostgreSQL table."""
    cols = VendedorPostgres.get_table_columns(table)
    return {"table": table, "columns": cols}


@router.get("/api/vendedor/ativos")
async def get_vendedores_ativos():
    """Get list of active salespersons from usuarios table."""
    try:
        results = VendedorPostgres.get_vendedores_ativos()
        if not results:
            logger.warning("No vendedores found in database")
            return []
        return results
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting active salespersons: {error_msg}", exc_info=True)
        # Return more detailed error for debugging
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {error_msg}. Check if USUARIOS table exists and database connection is working."
        )


@router.get("/api/vendedor/{cod_vendedor}/vendas")
async def get_vendas_by_day(
    cod_vendedor: int,
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get sales by day for a specific vendor."""
    try:
        results = VendedorPostgres.get_vendas_by_day(cod_vendedor, data_ini, data_fim)
        # Return empty list if no data (don't raise error for date ranges with no sales)
        return results if results else []
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting sales by day: {error_msg}", exc_info=True)
        # Return empty list instead of 500 for date ranges with no data
        return []


@router.get("/api/vendedor/{cod_vendedor}/vendas/{nf_interno}/items")
async def get_vendas_items_by_nf(cod_vendedor: int, nf_interno: int):
    """Get items for a specific invoice."""
    try:
        results = VendedorPostgres.get_vendas_items_by_nf(nf_interno)
        # Return empty list if no items found (don't raise error)
        return results if results else []
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting invoice items: {error_msg}", exc_info=True)
        # Return empty list instead of 500 for invoices with no items or query errors
        return []


@router.get("/api/vendedor/{cod_vendedor}/vendas/monthly")
async def get_vendas_monthly_summary(
    cod_vendedor: int,
    ano: int = Query(..., description="Year (YYYY)")
):
    """Get monthly sales summary for Metas comparison."""
    try:
        results = VendedorPostgres.get_vendas_monthly_summary(cod_vendedor, ano)
        # Return empty list if no data (don't raise error for years with no sales)
        return results if results else []
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting monthly sales summary: {error_msg}", exc_info=True)
        # Return empty list instead of 500 for years with no data
        return []


@router.get("/api/vendedor/{cod_vendedor}/metas")
async def get_metas(cod_vendedor: int, ano: int = Query(..., description="Year (YYYY)")):
    """Get metas (targets) for a salesperson."""
    try:
        meta = await engine.find_one(
            VendedorMetas,
            VendedorMetas.cod_vendedor == cod_vendedor
        )
        if not meta:
            # Return empty metas structure
            return {
                "cod_vendedor": cod_vendedor,
                "metas_mensais": []
            }
        
        # Filter metas for the requested year and convert to dict
        metas_ano = [m for m in meta.metas_mensais if m.ano == ano]
        metas_list = []
        for m in metas_ano:
            meta_dict = {
                "mes": m.mes,
                "ano": m.ano,
                "meta_1_2": None,
                "meta_1_5": None
            }
            if m.meta_1_2:
                try:
                    meta_dict["meta_1_2"] = float(str(m.meta_1_2))
                except:
                    meta_dict["meta_1_2"] = None
            if m.meta_1_5:
                try:
                    meta_dict["meta_1_5"] = float(str(m.meta_1_5))
                except:
                    meta_dict["meta_1_5"] = None
            metas_list.append(meta_dict)
        
        return {
            "cod_vendedor": meta.cod_vendedor,
            "nom_vendedor": meta.nom_vendedor,
            "metas_mensais": metas_list
        }
    except Exception as e:
        logger.error(f"Error getting metas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/vendedor/{cod_vendedor}/metas")
async def save_metas(
    cod_vendedor: int,
    metas: List[dict] = Body(...)
):
    """Save metas (targets) for a salesperson."""
    try:
        existing = await engine.find_one(
            VendedorMetas,
            VendedorMetas.cod_vendedor == cod_vendedor
        )
        
        # Convert dict list to MetaMensal objects
        metas_objects = []
        for m in metas:
            from bson import Decimal128
            metas_objects.append(MetaMensal(
                mes=int(m.get('mes', 0)),
                ano=int(m.get('ano', datetime.now().year)),
                meta_1_2=Decimal128(str(m.get('meta_1_2', 0))) if m.get('meta_1_2') else None,
                meta_1_5=Decimal128(str(m.get('meta_1_5', 0))) if m.get('meta_1_5') else None
            ))
        
        if existing:
            # Update existing
            existing.metas_mensais = metas_objects
            existing.data_atualizacao = datetime.now()
            await engine.save(existing)
        else:
            # Create new
            # Get vendedor name from usuarios table
            vendedores = VendedorPostgres.get_vendedores_ativos()
            nom_vendedor = next(
                (v['nom_vendedor'] for v in vendedores if v['cod_vendedor'] == cod_vendedor),
                None
            )
            
            new_meta = VendedorMetas(
                cod_vendedor=cod_vendedor,
                nom_vendedor=nom_vendedor,
                metas_mensais=metas_objects,
                data_criacao=datetime.now(),
                data_atualizacao=datetime.now()
            )
            await engine.save(new_meta)
        
        return {"status": "success", "message": "Metas salvas com sucesso"}
    except Exception as e:
        logger.error(f"Error saving metas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vendedor/grupo")
async def get_vendedor_grupo():
    """Get the current selected group of salespersons."""
    try:
        grupo = await engine.find_one(VendedorGrupo)
        if not grupo:
            return {"vendedores_selecionados": []}
        return {
            "nome_grupo": grupo.nome_grupo,
            "vendedores_selecionados": grupo.vendedores_selecionados
        }
    except Exception as e:
        logger.error(f"Error getting vendedor grupo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/vendedor/grupo")
async def save_vendedor_grupo(
    vendedores_selecionados: List[int] = Body(..., embed=True),
    nome_grupo: Optional[str] = Body(None, embed=True)
):
    """Save the selected group of salespersons."""
    try:
        existing = await engine.find_one(VendedorGrupo)
        
        if existing:
            existing.vendedores_selecionados = vendedores_selecionados
            if nome_grupo:
                existing.nome_grupo = nome_grupo
            existing.data_atualizacao = datetime.now()
            await engine.save(existing)
        else:
            new_grupo = VendedorGrupo(
                nome_grupo=nome_grupo or "Grupo Padrão",
                vendedores_selecionados=vendedores_selecionados,
                data_criacao=datetime.now(),
                data_atualizacao=datetime.now()
            )
            await engine.save(new_grupo)
        
        return {"status": "success", "message": "Grupo salvo com sucesso"}
    except Exception as e:
        logger.error(f"Error saving vendedor grupo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/metas/config/{ano}/{mes}")
async def get_metas_config(ano: int, mes: int):
    """Get Metas configuration for a specific year and month.
    If no config exists, tries to inherit from previous month.
    """
    try:
        config = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        if not config:
            logger.info(f"DEBUG: No config found for {ano}/{mes}, trying to inherit from previous months")
            prev_config = None
            search_mes = mes
            search_ano = ano
            for _ in range(12):
                search_mes -= 1
                if search_mes < 1:
                    search_mes = 12
                    search_ano -= 1
                prev_config = await engine.find_one(
                    VendedorConfigMetas,
                    (VendedorConfigMetas.ano == search_ano) & (VendedorConfigMetas.mes == search_mes)
                )
                if prev_config:
                    break
            
            if prev_config:
                logger.info(f"DEBUG: Found previous config ({search_ano}/{search_mes}), inheriting vendedores_ativos and vendedores_tipo")
                # Inherit vendedores_ativos and vendedores_tipo from previous month
                # But update the ano in vendedores_tipo to current year
                vendedores_tipo_list = []
                for vt in prev_config.vendedores_tipo:
                    vendedores_tipo_list.append({
                        "cod_vendedor": vt.cod_vendedor,
                        "tipo": vt.tipo,
                        "ano": ano  # Update to current year
                    })
                
                return {
                    "ano": ano,
                    "mes": mes,
                    "vendedores_tipo": vendedores_tipo_list,
                    "vendedores_ativos": prev_config.vendedores_ativos or [],
                    "margem_padrao": float(str(prev_config.margem_padrao)) if prev_config.margem_padrao else 0.10,
                    "meta_1": float(str(prev_config.meta_1)) if prev_config.meta_1 else 1.2,
                    "meta_2": float(str(prev_config.meta_2)) if prev_config.meta_2 else 1.5,
                    "meta_3": float(str(prev_config.meta_3)) if prev_config.meta_3 else None,
                    "meta_4": float(str(prev_config.meta_4)) if prev_config.meta_4 else None,
                    "meta_5": float(str(prev_config.meta_5)) if prev_config.meta_5 else None,
                    "metas_liberadas": getattr(prev_config, "metas_liberadas", False),
                }
            
            # No previous month config, return defaults
            logger.info(f"DEBUG: No previous month config found, returning defaults")
            return {
                "ano": ano,
                "mes": mes,
                "vendedores_tipo": [],
                "vendedores_ativos": [],
                "margem_padrao": 0.10,
                "meta_1": 1.2,
                "meta_2": 1.5,
                "meta_3": None,
                "meta_4": None,
                "meta_5": None,
                "metas_liberadas": False,
            }
        
        vendedores_tipo_list = [
            {"cod_vendedor": vt.cod_vendedor, "tipo": vt.tipo, "ano": vt.ano}
            for vt in config.vendedores_tipo
        ]
        logger.info(f"DEBUG: Config found for {ano}/{mes}: {len(vendedores_tipo_list)} vendedores_tipo, {len(config.vendedores_ativos)} vendedores_ativos")
        
        return {
            "ano": config.ano,
            "mes": config.mes,
            "vendedores_tipo": vendedores_tipo_list,
            "vendedores_ativos": config.vendedores_ativos,
            "margem_padrao": float(str(config.margem_padrao)),
            "meta_1": float(str(config.meta_1)) if config.meta_1 else 1.2,
            "meta_2": float(str(config.meta_2)) if config.meta_2 else 1.5,
            "meta_3": float(str(config.meta_3)) if config.meta_3 else None,
            "meta_4": float(str(config.meta_4)) if config.meta_4 else None,
            "meta_5": float(str(config.meta_5)) if config.meta_5 else None,
            "metas_liberadas": getattr(config, "metas_liberadas", False),
        }
    except Exception as e:
        logger.error(f"Error getting metas config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/metas/config/{ano}/{mes}")
async def save_metas_config(
    ano: int,
    mes: int,
    config: dict = Body(...)
):
    """Save Metas configuration for a specific year and month."""
    try:
        existing = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        
        vendedores_tipo = [
            VendedorTipo(
                cod_vendedor=vt["cod_vendedor"],
                tipo=vt["tipo"],
                ano=vt.get("ano", ano)
            )
            for vt in config.get("vendedores_tipo", [])
        ]
        
        logger.info(f"DEBUG: Saving config for {ano}/{mes}: {len(vendedores_tipo)} vendedores_tipo entries")
        for vt in vendedores_tipo:
            logger.info(f"DEBUG:   - Vendedor {vt.cod_vendedor}: {vt.tipo} (ano={vt.ano})")
        
        metas_liberadas = config.get("metas_liberadas", False)
        if existing:
            existing.vendedores_tipo = vendedores_tipo
            existing.vendedores_ativos = config.get("vendedores_ativos", [])
            existing.margem_padrao = Decimal128(str(config.get("margem_padrao", 0.10)))
            existing.meta_1 = Decimal128(str(config.get("meta_1", 1.2)))
            existing.meta_2 = Decimal128(str(config.get("meta_2", 1.5)))
            existing.meta_3 = Decimal128(str(config.get("meta_3"))) if config.get("meta_3") else None
            existing.meta_4 = Decimal128(str(config.get("meta_4"))) if config.get("meta_4") else None
            existing.meta_5 = Decimal128(str(config.get("meta_5"))) if config.get("meta_5") else None
            existing.metas_liberadas = metas_liberadas
            existing.data_atualizacao = datetime.now()
            await engine.save(existing)
        else:
            new_config = VendedorConfigMetas(
                ano=ano,
                mes=mes,
                vendedores_tipo=vendedores_tipo,
                vendedores_ativos=config.get("vendedores_ativos", []),
                margem_padrao=Decimal128(str(config.get("margem_padrao", 0.10))),
                meta_1=Decimal128(str(config.get("meta_1", 1.2))),
                meta_2=Decimal128(str(config.get("meta_2", 1.5))),
                meta_3=Decimal128(str(config.get("meta_3"))) if config.get("meta_3") else None,
                meta_4=Decimal128(str(config.get("meta_4"))) if config.get("meta_4") else None,
                meta_5=Decimal128(str(config.get("meta_5"))) if config.get("meta_5") else None,
                metas_liberadas=metas_liberadas,
            )
            await engine.save(new_config)

        # Sync metas_por_vendedor to VendedorMetas so Vendedores tab shows same values
        metas_por_vendedor = config.get("metas_por_vendedor") or {}
        synced_count = 0
        logger.info(f"DEBUG save_metas_config {ano}/{mes}: metas_por_vendedor keys={list(metas_por_vendedor.keys())[:5]}{'...' if len(metas_por_vendedor) > 5 else ''} count={len(metas_por_vendedor)}")
        if not metas_por_vendedor:
            logger.info(f"DEBUG save_metas_config {ano}/{mes}: metas_por_vendedor empty, skipping sync (existing VendedorMetas for this period are preserved)")
        if metas_por_vendedor:
            vendedores = VendedorPostgres.get_vendedores_ativos()
            nom_by_cod = {v["cod_vendedor"]: v.get("nom_vendedor") for v in vendedores if v.get("cod_vendedor")}
            for cod_key, metas in metas_por_vendedor.items():
                try:
                    cod_vendedor = int(cod_key) if cod_key is not None else None
                    if cod_vendedor is None:
                        continue
                    meta_1 = metas.get("meta_1")
                    meta_2 = metas.get("meta_2")
                    if meta_1 is None and meta_2 is None:
                        continue
                    existing_vm = await engine.find_one(
                        VendedorMetas,
                        VendedorMetas.cod_vendedor == cod_vendedor
                    )
                    other_meses = []
                    if existing_vm:
                        other_meses = [
                            m for m in existing_vm.metas_mensais
                            if not (m.ano == ano and m.mes == mes)
                        ]
                    meta_1_2 = Decimal128(str(meta_1)) if meta_1 is not None else None
                    meta_1_5 = Decimal128(str(meta_2)) if meta_2 is not None else None
                    new_entry = MetaMensal(mes=mes, ano=ano, meta_1_2=meta_1_2, meta_1_5=meta_1_5)
                    metas_mensais = other_meses + [new_entry]
                    if existing_vm:
                        existing_vm.metas_mensais = metas_mensais
                        existing_vm.data_atualizacao = datetime.now()
                        await engine.save(existing_vm)
                    else:
                        new_vm = VendedorMetas(
                            cod_vendedor=cod_vendedor,
                            nom_vendedor=nom_by_cod.get(cod_vendedor),
                            metas_mensais=metas_mensais,
                        )
                        await engine.save(new_vm)
                    synced_count += 1
                    if synced_count == 1:
                        logger.info(f"DEBUG save_metas_config {ano}/{mes}: first saved cod={cod_vendedor} meta_1={meta_1} meta_2={meta_2}")
                except Exception as e:
                    logger.warning(f"Sync metas_por_vendedor for cod_key={cod_key}: {e}", exc_info=True)
            logger.info(f"DEBUG save_metas_config {ano}/{mes}: synced {synced_count} vendedores to VendedorMetas (MongoDB)")

        return {"status": "success", "message": "Configuração salva com sucesso", "metas_synced": synced_count}
    except Exception as e:
        logger.error(f"Error saving metas config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/metas/clear/{ano}/{mes}")
async def clear_metas_mes(ano: int, mes: int):
    """Clear all saved per-vendedor metas (meta_1, meta_2) for the given month.
    Config for the month is left unchanged. Use to fix inconsistent data (e.g. Feb 2026).
    """
    try:
        all_vm = await engine.find(VendedorMetas)
        cleared = 0
        for vm in all_vm:
            original = getattr(vm, "metas_mensais", []) or []
            remaining = [m for m in original if not (getattr(m, "ano", None) == ano and getattr(m, "mes", None) == mes)]
            if len(remaining) != len(original):
                vm.metas_mensais = remaining
                vm.data_atualizacao = datetime.now()
                await engine.save(vm)
                cleared += 1
        logger.info(f"Cleared metas for {ano}/{mes}: {cleared} vendedores updated")
        return {"status": "success", "message": f"Metas de {ano}/{mes} limpas.", "cleared_count": cleared}
    except Exception as e:
        logger.error(f"Error clearing metas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_slug(nome: str) -> str:
    """Generate a slug from seller name: lowercase first name + 5 random digits."""
    nome_clean = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    nome_clean = re.sub(r'[^a-zA-Z\s]', '', nome_clean).strip().lower()
    first_name = nome_clean.split()[0] if nome_clean.split() else 'vendedor'
    digits = str(random.randint(10000, 99999))
    return f"{first_name}{digits}"


@router.get("/api/painel/slugs")
async def list_all_slugs():
    """List all seller slugs (admin view)."""
    try:
        slugs = await engine.find(VendedorSlug)
        return [
            {
                "cod_vendedor": s.cod_vendedor,
                "nom_vendedor": s.nom_vendedor,
                "slug": s.slug,
                "ativo": s.ativo,
                "url": f"/painel/{s.slug}",
            }
            for s in slugs
        ]
    except Exception as e:
        logger.error(f"Error listing slugs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/painel/slugs/generate")
async def generate_slugs_for_active():
    """Generate slugs for all sellers who have sales this month (or all active)."""
    try:
        hoje = date.today()
        vendedores_com_vendas = VendedorPostgres.get_vendedores_com_vendas_mes(hoje.year, hoje.month)
        
        existing_slugs = await engine.find(VendedorSlug)
        existing_map = {s.cod_vendedor: s for s in existing_slugs}
        existing_slug_values = {s.slug for s in existing_slugs}
        
        created = []
        for v in vendedores_com_vendas:
            cod = v['cod_vendedor']
            if cod in existing_map:
                continue
            
            nome = v.get('nom_vendedor') or f'Vendedor{cod}'
            slug = _generate_slug(nome)
            while slug in existing_slug_values:
                slug = _generate_slug(nome)
            
            new_slug = VendedorSlug(
                cod_vendedor=cod,
                nom_vendedor=nome,
                slug=slug,
                ativo=True,
            )
            await engine.save(new_slug)
            existing_slug_values.add(slug)
            created.append({"cod_vendedor": cod, "nom_vendedor": nome, "slug": slug})
        
        return {"created": len(created), "slugs": created}
    except Exception as e:
        logger.error(f"Error generating slugs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/painel/slugs/{cod_vendedor}")
async def create_or_regenerate_slug(cod_vendedor: int):
    """Create or regenerate slug for a specific seller."""
    try:
        all_vendedores = VendedorPostgres.get_vendedores_ativos()
        vendedor_info = next((v for v in all_vendedores if v.get('cod_vendedor') == cod_vendedor), None)
        nome = vendedor_info.get('nom_vendedor', f'Vendedor{cod_vendedor}') if vendedor_info else f'Vendedor{cod_vendedor}'
        
        existing = await engine.find_one(VendedorSlug, VendedorSlug.cod_vendedor == cod_vendedor)
        existing_slugs = await engine.find(VendedorSlug)
        existing_slug_values = {s.slug for s in existing_slugs}
        
        slug = _generate_slug(nome)
        while slug in existing_slug_values:
            slug = _generate_slug(nome)
        
        if existing:
            existing.slug = slug
            existing.nom_vendedor = nome
            existing.data_atualizacao = datetime.now()
            await engine.save(existing)
        else:
            new_slug = VendedorSlug(
                cod_vendedor=cod_vendedor,
                nom_vendedor=nome,
                slug=slug,
                ativo=True,
            )
            await engine.save(new_slug)
        
        return {"cod_vendedor": cod_vendedor, "slug": slug, "url": f"/painel/{slug}"}
    except Exception as e:
        logger.error(f"Error creating slug: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/painel/{slug}")
async def get_painel_vendedor(slug: str, ano: Optional[int] = None, mes: Optional[int] = None):
    """
    Public seller dashboard endpoint. No auth needed - slug acts as token.
    Returns all data needed for the seller's dashboard.
    """
    try:
        slug_doc = await engine.find_one(VendedorSlug, VendedorSlug.slug == slug)
        if not slug_doc:
            raise HTTPException(status_code=404, detail="Vendedor não encontrado")
        
        cod_vendedor = slug_doc.cod_vendedor
        nom_vendedor = slug_doc.nom_vendedor
        
        hoje = date.today()
        target_ano = ano or hoje.year
        target_mes = mes or hoje.month
        
        dias_no_mes = calendar.monthrange(target_ano, target_mes)[1]
        is_current_month = (target_ano == hoje.year and target_mes == hoje.month)
        dia_atual = hoje.day if is_current_month else dias_no_mes
        
        daily_sales = VendedorPostgres.get_vendas_diarias_mes(cod_vendedor, target_ano, target_mes)
        daily_map = {int(d['dia']): float(d['vlr_dia']) for d in daily_sales}
        
        dias = []
        vendas_diarias = []
        vendas_cumulativas = []
        acumulado = 0.0
        for dia in range(1, dia_atual + 1):
            vlr = daily_map.get(dia, 0.0)
            acumulado += vlr
            dias.append(dia)
            vendas_diarias.append(round(vlr, 2))
            vendas_cumulativas.append(round(acumulado, 2))
        
        total_vendas = acumulado
        comissao_1pct = round(total_vendas * 0.01, 2)
        
        meta_1_value = 0.0
        meta_2_value = 0.0
        meta_final = 0.0
        metas_liberadas = False
        try:
            config = await engine.find_one(
                VendedorConfigMetas,
                (VendedorConfigMetas.ano == target_ano) & (VendedorConfigMetas.mes == target_mes)
            )
            if config:
                metas_liberadas = getattr(config, "metas_liberadas", False)
                metas_calc = await _calcular_metas_internal(target_ano, target_mes, config)
                await _apply_saved_metas_overrides(metas_calc, target_ano, target_mes)
                vendedores_tipo = getattr(config, 'vendedores_tipo', None) or []
                tipo_info = next(
                    (vt for vt in vendedores_tipo if getattr(vt, 'cod_vendedor', None) == cod_vendedor),
                    None
                )
                tipo = getattr(tipo_info, 'tipo', 'Calçado') if tipo_info else 'Calçado'
                
                group_key = 'roupa' if tipo == 'Roupa' else ('loja' if tipo == 'Loja' else 'calcado')
                group = metas_calc.get(group_key, {})
                
                detalhes = group.get('vendedores_detalhes', [])
                seller_detail = next((d for d in detalhes if d.get('cod_vendedor') == cod_vendedor), None)
                if seller_detail:
                    meta_1_value = seller_detail.get('meta_1', 0)
                    meta_2_value = seller_detail.get('meta_2', 0)
                else:
                    meta_1_value = group.get('meta_1', 0)
                    meta_2_value = group.get('meta_2', 0)
                meta_final = group.get('meta_base', 0)
        except Exception as e:
            logger.warning(f"Error getting metas for painel: {str(e)}")
        if not metas_liberadas:
            meta_1_value = meta_2_value = meta_final = 0.0
        meta_1_proporcional = meta_1_value * (dia_atual / dias_no_mes) if meta_1_value > 0 else 0
        meta_2_proporcional = meta_2_value * (dia_atual / dias_no_mes) if meta_2_value > 0 else 0
        
        pct_meta_1 = round((total_vendas / meta_1_proporcional) * 100, 1) if meta_1_proporcional > 0 else 0
        pct_meta_2 = round((total_vendas / meta_2_proporcional) * 100, 1) if meta_2_proporcional > 0 else 0
        
        falta_meta_1 = max(0, meta_1_value - total_vendas)
        falta_meta_2 = max(0, meta_2_value - total_vendas)
        dias_restantes = dias_no_mes - dia_atual
        por_dia_meta_1 = round(falta_meta_1 / dias_restantes, 2) if dias_restantes > 0 else 0
        por_dia_meta_2 = round(falta_meta_2 / dias_restantes, 2) if dias_restantes > 0 else 0
        
        dias_uteis_passados = dia_atual
        ritmo_atual = round(total_vendas / dias_uteis_passados, 2) if dias_uteis_passados > 0 else 0
        
        meses_disponiveis = []
        try:
            monthly = VendedorPostgres.get_vendas_monthly_summary(cod_vendedor, target_ano)
            for m in monthly:
                meses_disponiveis.append({
                    "mes": int(m['mes']),
                    "ano": target_ano,
                    "mes_ano": m['mes_ano'],
                    "total": float(m['vlr_liquido_total'])
                })
            if target_ano == hoje.year:
                prev_year_monthly = VendedorPostgres.get_vendas_monthly_summary(cod_vendedor, target_ano - 1)
                for m in prev_year_monthly:
                    meses_disponiveis.append({
                        "mes": int(m['mes']),
                        "ano": target_ano - 1,
                        "mes_ano": m['mes_ano'],
                        "total": float(m['vlr_liquido_total'])
                    })
        except Exception:
            pass
        
        return {
            "cod_vendedor": cod_vendedor,
            "nom_vendedor": nom_vendedor,
            "ano": target_ano,
            "mes": target_mes,
            "dia_atual": dia_atual,
            "dias_no_mes": dias_no_mes,
            "total_vendas": round(total_vendas, 2),
            "comissao_1pct": comissao_1pct,
            "meta_1": round(meta_1_value, 2),
            "meta_2": round(meta_2_value, 2),
            "meta_final": round(meta_final, 2),
            "meta_1_proporcional": round(meta_1_proporcional, 2),
            "meta_2_proporcional": round(meta_2_proporcional, 2),
            "pct_meta_1": pct_meta_1,
            "pct_meta_2": pct_meta_2,
            "falta_meta_1": round(falta_meta_1, 2),
            "falta_meta_2": round(falta_meta_2, 2),
            "por_dia_meta_1": por_dia_meta_1,
            "por_dia_meta_2": por_dia_meta_2,
            "ritmo_atual": ritmo_atual,
            "dias_restantes": dias_restantes,
            "dias": dias,
            "vendas_diarias": vendas_diarias,
            "vendas_cumulativas": vendas_cumulativas,
            "meses_disponiveis": sorted(meses_disponiveis, key=lambda m: (m['ano'], m['mes'])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in painel vendedor: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vendedor/ativos-mes")
async def get_vendedores_ativos_mes(ano: Optional[int] = None, mes: Optional[int] = None):
    """Get sellers with sales in a given month. Defaults to current month."""
    hoje = date.today()
    target_ano = ano or hoje.year
    target_mes = mes or hoje.month
    try:
        results = VendedorPostgres.get_vendedores_com_vendas_mes(target_ano, target_mes)
        slugs = await engine.find(VendedorSlug)
        slug_map = {s.cod_vendedor: s.slug for s in slugs}
        
        for r in results:
            cod = r['cod_vendedor']
            r['slug'] = slug_map.get(cod)
            r['url'] = f"/painel/{slug_map[cod]}" if cod in slug_map else None
            r['total_vendas'] = float(r.get('total_vendas', 0))
        return results
    except Exception as e:
        logger.error(f"Error getting active sellers for month: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _get_tipo_map_for_ano_mes(ano: int, mes: int) -> Dict[int, str]:
    """Load config for ano/mes and return cod_vendedor -> tipo. Used for tipo-per-year: anterior for sales grouping, atual for metas.
    Searches all 12 months of the given ano (never goes to ano-1) so we get tipo for that year.
    Filters vendedores_tipo by vt.ano == ano when present, so we use the correct year's assignment.
    """
    try:
        cfg = None
        for m in range(12):
            search_mes = ((mes - 1 - m) % 12) + 1
            search_ano = ano
            cfg = await engine.find_one(
                VendedorConfigMetas,
                (VendedorConfigMetas.ano == search_ano) & (VendedorConfigMetas.mes == search_mes)
            )
            if cfg and getattr(cfg, 'vendedores_tipo', None):
                break
        if not cfg or not getattr(cfg, 'vendedores_tipo', None):
            return {}
        out = {}
        for vt in cfg.vendedores_tipo:
            vt_ano = getattr(vt, 'ano', None)
            if vt_ano is not None and int(vt_ano) != ano:
                continue
            cod = getattr(vt, 'cod_vendedor', None)
            tipo = getattr(vt, 'tipo', None)
            if cod is not None and tipo:
                out[cod] = tipo
        if not out:
            for vt in cfg.vendedores_tipo:
                cod = getattr(vt, 'cod_vendedor', None)
                tipo = getattr(vt, 'tipo', None)
                if cod is not None and tipo:
                    out[cod] = tipo
        return out
    except Exception as e:
        logger.debug("_get_tipo_map_for_ano_mes %s/%s: %s", ano, mes, e)
        return {}


async def _calcular_metas_internal(ano: int, mes: int, config: VendedorConfigMetas):
    """Internal function to calculate metas. Returns breakdown by tipo group.
    Seller tipo is per year: use tipo from ano_anterior for grouping last year's sales,
    tipo from ano (current) for which group each seller appears in and their metas.
    """
    ano_anterior = ano - 1

    # --- 1. Parse config values FIRST ---
    vendedores_tipo = getattr(config, 'vendedores_tipo', None) or []

    margem_val = getattr(config, 'margem_padrao', None)
    try:
        margem = float(str(margem_val)) if margem_val is not None else 0.1
    except (ValueError, TypeError):
        margem = 0.1

    meta_vals = {}
    for key in ('meta_1', 'meta_2', 'meta_3', 'meta_4', 'meta_5'):
        raw = getattr(config, key, None)
        try:
            meta_vals[key] = float(str(raw)) if raw is not None else None
        except (ValueError, TypeError):
            meta_vals[key] = None
    if meta_vals['meta_1'] is None:
        meta_vals['meta_1'] = 1.05
    if meta_vals['meta_2'] is None:
        meta_vals['meta_2'] = 1.10

    # --- 2. Active sellers filter (only these count in media/metas) ---
    vendedores_ativos_set = set()
    vendedores_ativos_raw = getattr(config, 'vendedores_ativos', None) or []
    for cod in vendedores_ativos_raw:
        try:
            vendedores_ativos_set.add(int(cod))
        except (TypeError, ValueError):
            pass

    # --- 3. Build tipo lookups: anterior (for sales grouping) and atual (for metas/display) ---
    # tipo_map_atual: from current year config (so CRIS B in Calçado 2026 shows in Calçado)
    # tipo_map_anterior: from previous year config (so CRIS B's 2025 sales go to Roupa if she was Roupa in 2025)
    tipo_map_atual = await _get_tipo_map_for_ano_mes(ano, mes)
    if not tipo_map_atual:
        for vt in vendedores_tipo:
            cod = getattr(vt, 'cod_vendedor', None)
            tipo = getattr(vt, 'tipo', None)
            if cod is not None and tipo:
                tipo_map_atual[cod] = tipo
    tipo_map_anterior = await _get_tipo_map_for_ano_mes(ano_anterior, mes)
    if not tipo_map_anterior:
        tipo_map_anterior = dict(tipo_map_atual)

    # --- 4. Get all vendedores info (names) ---
    all_vendedores = VendedorPostgres.get_vendedores_ativos()
    names = {v['cod_vendedor']: v.get('nom_vendedor', f"Vendedor {v['cod_vendedor']}") for v in all_vendedores if v.get('cod_vendedor') is not None}

    # --- 5. Find all vendedores with sales in previous year for target month (all for table; ativo used only for media) ---
    vendedores_com_vendas = {}
    for v in all_vendedores:
        cod = v.get('cod_vendedor')
        if cod is None:
            continue
        try:
            monthly = VendedorPostgres.get_vendas_monthly_summary(cod, ano_anterior)
            if monthly:
                for s in monthly:
                    s_mes = s.get('mes')
                    if s_mes is not None and int(s_mes) == mes:
                        vlr = float(s.get('vlr_liquido_total', 0) or 0)
                        if vlr > 0:
                            vendedores_com_vendas[cod] = vlr
                        break
        except Exception:
            continue

    # --- 6. Round up to nearest 1000 ---
    def round_up_1000(x: float) -> float:
        if x <= 0:
            return 0.0
        return float(math.ceil(x / 1000.0) * 1000)

    mult_meta_1 = float(meta_vals['meta_1']) if meta_vals.get('meta_1') is not None else 1.05
    mult_meta_2 = float(meta_vals['meta_2']) if meta_vals.get('meta_2') is not None else 1.10

    # --- 7. Sales grouped by tipo_anterior (last year) — for group totals ---
    sales_by_tipo_anterior = {'Calçado': 0.0, 'Roupa': 0.0, 'Loja': 0.0}
    for cod, vendedor_sales in vendedores_com_vendas.items():
        tipo_ant = tipo_map_anterior.get(cod, 'Calçado')
        if tipo_ant not in sales_by_tipo_anterior:
            tipo_ant = 'Calçado'
        sales_by_tipo_anterior[tipo_ant] += vendedor_sales

    # --- 8. Vendedores_detalhes grouped by tipo_atual (this year) — for metas/display ---
    groups = {
        'Calçado': {'sales': 0.0, 'detalhes': [], 'cods': []},
        'Roupa':   {'sales': 0.0, 'detalhes': [], 'cods': []},
        'Loja':    {'sales': 0.0, 'detalhes': [], 'cods': []},
    }
    added_cods = set()
    for vt in vendedores_tipo:
        cod = getattr(vt, 'cod_vendedor', None)
        if cod is None:
            continue
        tipo_atual = tipo_map_atual.get(cod, getattr(vt, 'tipo', None) or 'Calçado')
        if tipo_atual not in groups:
            tipo_atual = 'Calçado'
        ativo = not vendedores_ativos_set or cod in vendedores_ativos_set
        vlr = round(vendedores_com_vendas.get(cod, 0.0), 2)
        added_cods.add(cod)
        groups[tipo_atual]['cods'].append(cod)
        groups[tipo_atual]['detalhes'].append({
            "cod_vendedor": cod,
            "nom_vendedor": names.get(cod, f"Vendedor {cod}"),
            "tipo": tipo_atual,
            "ativo": ativo,
            "vlr_sales_anterior": vlr,
            "meta_1": None,
            "meta_2": None,
            "mes_ano": f"{ano_anterior}-{mes:02d}",
        })
    for cod, vendedor_sales in vendedores_com_vendas.items():
        if cod in added_cods:
            continue
        tipo_atual = tipo_map_atual.get(cod, tipo_map_anterior.get(cod, 'Calçado'))
        if tipo_atual not in groups:
            tipo_atual = 'Calçado'
        ativo = not vendedores_ativos_set or cod in vendedores_ativos_set
        added_cods.add(cod)
        groups[tipo_atual]['cods'].append(cod)
        groups[tipo_atual]['detalhes'].append({
            "cod_vendedor": cod,
            "nom_vendedor": names.get(cod, f"Vendedor {cod}"),
            "tipo": tipo_atual,
            "ativo": ativo,
            "vlr_sales_anterior": round(vendedor_sales, 2),
            "meta_1": None,
            "meta_2": None,
            "mes_ano": f"{ano_anterior}-{mes:02d}",
        })

    # --- 9. Group stats: sales_anterior from tipo_anterior; media = sales_anterior / active_count (tipo_atual); meta = round_up(media * mult) ---
    def build_group_result(grp_data, tipo_label, sales_anterior_from_anterior: float):
        detalhes = grp_data['detalhes']
        total_sales = sales_anterior_from_anterior
        active_count = sum(
            1 for d in detalhes
            if d.get('cod_vendedor') is not None and (not vendedores_ativos_set or d.get('cod_vendedor') in vendedores_ativos_set)
        )
        media = round(total_sales / active_count, 2) if active_count > 0 else 0.0
        grp_meta_1 = round_up_1000(media * mult_meta_1)
        grp_meta_2 = round_up_1000(media * mult_meta_2)
        meta_base = grp_meta_2
        for d in detalhes:
            d["meta_1"] = round(grp_meta_1, 2)
            d["meta_2"] = round(grp_meta_2, 2)
        count = len(detalhes)
        res = {
            "vendedores": grp_data['cods'],
            "vendedores_detalhes": detalhes,
            "count_atual": count,
            "sales_anterior": round(total_sales, 2),
            "media": media,
            "meta_base": meta_base,
            "meta_1": grp_meta_1,
            "meta_2": grp_meta_2,
            "margem_aplicada": margem,
            "fonte_calculo": f"Vendas de {ano_anterior}/{mes:02d} - Média por vendedor ativo, Meta = ×{mult_meta_1}/{mult_meta_2} (arred. 1000)",
        }
        for extra_key in ('meta_3', 'meta_4', 'meta_5'):
            mult = meta_vals.get(extra_key)
            if mult is not None:
                res[extra_key] = round(meta_base * mult, 2)
        return res, count, grp_meta_1, grp_meta_2, meta_base

    calc_res, calc_cnt, calc_m1, calc_m2, calc_mb = build_group_result(
        groups['Calçado'], 'Calçado', sales_by_tipo_anterior['Calçado'])
    roup_res, roup_cnt, roup_m1, roup_m2, roup_mb = build_group_result(
        groups['Roupa'], 'Roupa', sales_by_tipo_anterior['Roupa'])
    loja_res, loja_cnt, loja_m1, loja_m2, loja_mb = build_group_result(
        groups['Loja'], 'Loja', sales_by_tipo_anterior['Loja'])

    total_expected_1 = round(calc_m1 * calc_cnt + roup_m1 * roup_cnt + loja_m1 * loja_cnt, 2)
    total_expected_2 = round(calc_m2 * calc_cnt + roup_m2 * roup_cnt + loja_m2 * loja_cnt, 2)

    result = {
        "ano": ano,
        "mes": mes,
        "ano_anterior": ano_anterior,
        "calcado": calc_res,
        "roupa": roup_res,
        "loja": loja_res,
        "total_sales_anterior": round(
            sales_by_tipo_anterior['Calçado'] + sales_by_tipo_anterior['Roupa'] + sales_by_tipo_anterior['Loja'], 2),
        "total_expected_1": total_expected_1,
        "total_expected_2": total_expected_2,
    }
    for i, key in enumerate(['meta_3', 'meta_4', 'meta_5'], start=3):
        mult = meta_vals.get(key)
        if mult is not None:
            result[f"total_expected_{i}"] = round(
                calc_mb * mult * calc_cnt + roup_mb * mult * roup_cnt + loja_mb * mult * loja_cnt, 2
            )
    return result


async def _get_saved_metas_overrides(ano: int, mes: int) -> Dict[int, Dict]:
    """Return dict cod_vendedor -> {meta_1, meta_2} from VendedorMetas for this ano/mes."""
    overrides = {}
    try:
        all_vm = await engine.find(VendedorMetas)
        for vm in all_vm:
            cod = getattr(vm, "cod_vendedor", None)
            if cod is None:
                continue
            try:
                cod_int = int(cod)
            except (TypeError, ValueError):
                cod_int = cod
            for m in getattr(vm, "metas_mensais", []) or []:
                m_ano = getattr(m, "ano", None)
                m_mes = getattr(m, "mes", None)
                if m_ano == ano and m_mes == mes:
                    try:
                        meta_1 = float(str(m.meta_1_2)) if getattr(m, "meta_1_2", None) is not None else None
                        meta_2 = float(str(m.meta_1_5)) if getattr(m, "meta_1_5", None) is not None else None
                        if meta_1 is not None or meta_2 is not None:
                            overrides[cod_int] = {"meta_1": meta_1, "meta_2": meta_2}
                    except (TypeError, ValueError):
                        pass
                    break
    except Exception as e:
        logger.warning(f"Could not get saved metas overrides: {e}")
    return overrides


async def _get_config_doc_and_dict(ano: int, mes: int):
    """Get config document (for _calcular_metas_internal) and config dict (for API response).
    Tries current month, then previous months, then returns default in-memory config.
    """
    config = await engine.find_one(
        VendedorConfigMetas,
        (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
    )
    if config:
        vendedores_tipo_list = [
            {"cod_vendedor": vt.cod_vendedor, "tipo": vt.tipo, "ano": vt.ano}
            for vt in config.vendedores_tipo
        ]
        config_dict = {
            "ano": config.ano,
            "mes": config.mes,
            "vendedores_tipo": vendedores_tipo_list,
            "vendedores_ativos": config.vendedores_ativos or [],
            "margem_padrao": float(str(config.margem_padrao)),
            "meta_1": float(str(config.meta_1)) if config.meta_1 else 1.2,
            "meta_2": float(str(config.meta_2)) if config.meta_2 else 1.5,
            "meta_3": float(str(config.meta_3)) if config.meta_3 else None,
            "meta_4": float(str(config.meta_4)) if config.meta_4 else None,
            "meta_5": float(str(config.meta_5)) if config.meta_5 else None,
            "metas_liberadas": getattr(config, "metas_liberadas", False),
        }
        return config, config_dict

    search_mes, search_ano = mes, ano
    for _ in range(12):
        search_mes -= 1
        if search_mes < 1:
            search_mes = 12
            search_ano -= 1
        prev = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == search_ano) & (VendedorConfigMetas.mes == search_mes)
        )
        if prev:
            vendedores_tipo_list = [
                {"cod_vendedor": vt.cod_vendedor, "tipo": vt.tipo, "ano": ano}
                for vt in prev.vendedores_tipo
            ]
            config_dict = {
                "ano": ano,
                "mes": mes,
                "vendedores_tipo": vendedores_tipo_list,
                "vendedores_ativos": prev.vendedores_ativos or [],
                "margem_padrao": float(str(prev.margem_padrao)) if prev.margem_padrao else 0.10,
                "meta_1": float(str(prev.meta_1)) if prev.meta_1 else 1.2,
                "meta_2": float(str(prev.meta_2)) if prev.meta_2 else 1.5,
                "meta_3": float(str(prev.meta_3)) if prev.meta_3 else None,
                "meta_4": float(str(prev.meta_4)) if prev.meta_4 else None,
                "meta_5": float(str(prev.meta_5)) if prev.meta_5 else None,
                "metas_liberadas": getattr(prev, "metas_liberadas", False),
            }
            return prev, config_dict

    config_doc = VendedorConfigMetas(
        ano=ano,
        mes=mes,
        vendedores_tipo=[],
        vendedores_ativos=[],
        margem_padrao=Decimal128("0.10"),
        meta_1=Decimal128("1.2"),
        meta_2=Decimal128("1.5"),
    )
    config_dict = {
        "ano": ano,
        "mes": mes,
        "vendedores_tipo": [],
        "vendedores_ativos": [],
        "margem_padrao": 0.10,
        "meta_1": 1.2,
        "meta_2": 1.5,
        "meta_3": None,
        "meta_4": None,
        "meta_5": None,
        "metas_liberadas": False,
    }
    return config_doc, config_dict


async def _apply_saved_metas_overrides(result: dict, ano: int, mes: int) -> dict:
    """Overwrite meta_1/meta_2 in result with saved values from VendedorMetas for this ano/mes."""
    try:
        overrides = await _get_saved_metas_overrides(ano, mes)
        logger.info(f"DEBUG _apply_saved_metas_overrides {ano}/{mes}: overrides count={len(overrides)} keys={list(overrides.keys())[:5]}{'...' if len(overrides) > 5 else ''}")
        for group_key in ("calcado", "roupa", "loja"):
            group = result.get(group_key)
            if not group:
                continue
            detalhes = group.get("vendedores_detalhes") or []
            for v in detalhes:
                cod = v.get("cod_vendedor")
                if cod is None:
                    continue
                try:
                    cod_int = int(cod)
                except (TypeError, ValueError):
                    cod_int = cod
                if cod_int not in overrides:
                    continue
                o = overrides[cod_int]
                if o.get("meta_1") is not None:
                    v["meta_1"] = round(o["meta_1"], 2)
                if o.get("meta_2") is not None:
                    v["meta_2"] = round(o["meta_2"], 2)
        return result
    except Exception as e:
        logger.warning(f"Could not apply saved metas overrides: {e}")
        return result


@router.get("/api/metas/saved/{ano}/{mes}")
async def get_metas_saved(ano: int, mes: int):
    """
    Load saved state for Metas tab: config + per-vendedor meta_1/meta_2 from MongoDB.
    meta_1/meta_2 are only from saved values (null if not saved). Same table structure as calcular.
    Frontend uses this on open; "Estimar Metas" uses GET /api/metas/calcular to fill calculated values.
    """
    try:
        config_doc, config_dict = await _get_config_doc_and_dict(ano, mes)
        result = await _calcular_metas_internal(ano, mes, config_doc)
        overrides = await _get_saved_metas_overrides(ano, mes)
        for group_key in ("calcado", "roupa", "loja"):
            group = result.get(group_key)
            if not group:
                continue
            for v in group.get("vendedores_detalhes") or []:
                cod = v.get("cod_vendedor")
                if cod is None:
                    continue
                try:
                    cod_int = int(cod)
                except (TypeError, ValueError):
                    cod_int = cod
                o = overrides.get(cod_int, {})
                v["meta_1"] = round(o["meta_1"], 2) if o.get("meta_1") is not None else None
                v["meta_2"] = round(o["meta_2"], 2) if o.get("meta_2") is not None else None
        return {"config": config_dict, "metas_calculadas": result}
    except Exception as e:
        logger.error(f"Error getting metas saved: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _config_for_calcular(ano: int, mes: int, config: Optional[VendedorConfigMetas], body: Optional[dict]) -> VendedorConfigMetas:
    """Build config for _calcular_metas_internal. If body has vendedores_tipo/vendedores_ativos, use them (current UI state)."""
    base = config
    if not base:
        base = VendedorConfigMetas(
            ano=ano,
            mes=mes,
            vendedores_tipo=[],
            vendedores_ativos=[],
            margem_padrao=Decimal128("0.10"),
            meta_1=Decimal128("1.2"),
            meta_2=Decimal128("1.5")
        )
    if not body or (not body.get("vendedores_tipo") and body.get("vendedores_ativos") is None):
        return base
    # Override with request body (current screen state) so Estimar uses latest groups
    vendedores_tipo = body.get("vendedores_tipo")
    vendedores_ativos = body.get("vendedores_ativos")
    tipo_list = list(base.vendedores_tipo) if base.vendedores_tipo else []
    ativos_list = list(base.vendedores_ativos) if base.vendedores_ativos else []
    if vendedores_tipo is not None:
        tipo_list = [
            VendedorTipo(cod_vendedor=vt.get("cod_vendedor"), tipo=vt.get("tipo") or "Calçado", ano=vt.get("ano", ano))
            for vt in vendedores_tipo if vt.get("cod_vendedor") is not None
        ]
    if vendedores_ativos is not None:
        ativos_list = [int(x) for x in vendedores_ativos if x is not None]
    def _dec(v, default):
        if v is None:
            return Decimal128(str(default))
        return Decimal128(str(v))
    m1 = body.get("meta_1")
    m2 = body.get("meta_2")
    if m1 is None and hasattr(base, "meta_1") and base.meta_1 is not None:
        m1 = float(str(base.meta_1))
    if m2 is None and hasattr(base, "meta_2") and base.meta_2 is not None:
        m2 = float(str(base.meta_2))
    return VendedorConfigMetas(
        ano=ano,
        mes=mes,
        vendedores_tipo=tipo_list,
        vendedores_ativos=ativos_list,
        margem_padrao=_dec(body.get("margem_padrao"), getattr(base, "margem_padrao", 0.10) or 0.10),
        meta_1=_dec(m1, 1.2),
        meta_2=_dec(m2, 1.5),
        meta_3=Decimal128(str(body["meta_3"])) if body.get("meta_3") is not None else getattr(base, "meta_3", None),
        meta_4=Decimal128(str(body["meta_4"])) if body.get("meta_4") is not None else getattr(base, "meta_4", None),
        meta_5=Decimal128(str(body["meta_5"])) if body.get("meta_5") is not None else getattr(base, "meta_5", None),
    )


@router.get("/api/metas/calcular/{ano}/{mes}")
async def calcular_metas(ano: int, mes: int):
    """
    Calculate targets (Metas) for a specific month/year based on previous year sales.
    Uses config from DB. For current UI state (e.g. after group changes), use POST with body.
    """
    try:
        config = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        if not config:
            config = VendedorConfigMetas(
                ano=ano, mes=mes, vendedores_tipo=[], vendedores_ativos=[],
                margem_padrao=Decimal128("0.10"), meta_1=Decimal128("1.2"), meta_2=Decimal128("1.5")
            )
        result = await _calcular_metas_internal(ano, mes, config)
        result = await _apply_saved_metas_overrides(result, ano, mes)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/metas/calcular/{ano}/{mes}")
async def calcular_metas_post(ano: int, mes: int, body: Optional[dict] = Body(None)):
    """
    Calculate targets using optional body as current state (vendedores_tipo, vendedores_ativos).
    Use this so Estimar Metas uses the latest group/ativo changes from the UI without relying on save timing.
    """
    try:
        config_db = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        config = _config_for_calcular(ano, mes, config_db, body or {})
        result = await _calcular_metas_internal(ano, mes, config)
        result = await _apply_saved_metas_overrides(result, ano, mes)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metas (POST): {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/metas/atual/{ano}/{mes}")
async def get_metas_atual(ano: int, mes: int):
    """
    Get current month actual sales vs targets for all active sellers.
    Includes proportional target based on day of month.
    """
    # Verify function exists before using it
    try:
        # This will raise NameError if function doesn't exist
        _ = _calcular_metas_internal
    except NameError:
        logger.error("CRITICAL: _calcular_metas_internal function is not defined in module scope!")
        return {
            "ano": ano,
            "mes": mes,
            "dia_atual": None,
            "dias_no_mes": 31,
            "proporcao": 0,
            "vendedores": [],
            "metas_calculadas": None,
            "error": "_calcular_metas_internal function not available - server may need restart"
        }
    
    try:
        # Get config
        config = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        
        # If no config exists, create a default one (will default all to Calçado)
        if not config:
            logger.info(f"DEBUG: No config found for {ano}/{mes} in get_metas_atual, creating default")
            config = VendedorConfigMetas(
                ano=ano,
                mes=mes,
                vendedores_tipo=[],
                vendedores_ativos=[],
                margem_padrao=Decimal128("0.10"),
                meta_1=Decimal128("1.05"),
                meta_2=Decimal128("1.10")
            )
        
        # Calculate date range for current month
        try:
            data_ini = date(ano, mes, 1)
            if mes == 12:
                data_fim = date(ano + 1, 1, 1)
            else:
                data_fim = date(ano, mes + 1, 1)
            from datetime import timedelta
            data_fim = data_fim - timedelta(days=1)
            
            # Get today's date
            hoje = date.today()
            dia_atual = hoje.day if hoje.year == ano and hoje.month == mes else None
            dias_no_mes = (data_fim - data_ini).days + 1
            if dias_no_mes > 0:
                proporcao = dia_atual / dias_no_mes if dia_atual else 1.0
            else:
                proporcao = 1.0
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating date range for {ano}/{mes}: {str(e)}", exc_info=True)
            # Return empty structure if date calculation fails
            return {
                "ano": ano,
                "mes": mes,
                "dia_atual": None,
                "dias_no_mes": 31,
                "proporcao": 0,
                "vendedores": [],
                "metas_calculadas": None,
                "error": f"Invalid date: {str(e)}"
            }
        
        # Get calculated targets using internal function
        metas_calc = None
        try:
            metas_calc = await _calcular_metas_internal(ano, mes, config)
            if metas_calc:
                await _apply_saved_metas_overrides(metas_calc, ano, mes)
        except NameError as ne:
            logger.error(f"NameError in get_metas_atual: {str(ne)}. Function may not be defined. This should not happen if code is up to date.", exc_info=True)
            # Continue with None metas_calc - will handle gracefully below
        except Exception as e:
            logger.error(f"Error calculating metas in get_metas_atual: {str(e)}", exc_info=True)
            # Continue with None metas_calc - will handle gracefully below
        
        # Build tipo lookup from config and metas_calc
        vendedores_tipo = getattr(config, 'vendedores_tipo', None) or []
        tipo_map = {}
        if metas_calc:
            for group_key in ("calcado", "roupa", "loja"):
                for d in (metas_calc.get(group_key) or {}).get("vendedores_detalhes") or []:
                    cod = d.get("cod_vendedor")
                    if cod is not None:
                        tipo_map[cod] = d.get("tipo") or "Calçado"
        for vt in vendedores_tipo:
            cod = getattr(vt, 'cod_vendedor', None)
            if cod is not None:
                tipo_map[cod] = getattr(vt, 'tipo', None) or "Calçado"

        # Get ALL vendedores and their sales in the month; keep only those with any sale
        all_vendedores_info = VendedorPostgres.get_vendedores_ativos()
        vendedores_dict = {v.get('cod_vendedor'): v for v in all_vendedores_info}
        vendedores_data = []

        for v in all_vendedores_info:
            cod_vendedor = v.get('cod_vendedor')
            if cod_vendedor is None:
                continue
            try:
                sales = VendedorPostgres.get_vendas_by_day(
                    cod_vendedor,
                    data_ini.strftime("%Y-%m-%d"),
                    data_fim.strftime("%Y-%m-%d")
                )
                vlr_atual = sum(float(s.get('vlr_liquido_total', 0)) for s in sales) if sales else 0.0
            except Exception as e:
                logger.warning(f"Error getting sales for vendedor {cod_vendedor}: {str(e)}")
                vlr_atual = 0.0

            if vlr_atual <= 0:
                continue

            nom_vendedor = v.get('nom_vendedor') or f"Vendedor {cod_vendedor}"
            tipo = tipo_map.get(cod_vendedor, "Calçado")
            if tipo not in ("Calçado", "Roupa", "Loja"):
                tipo = "Calçado"

            # meta_final = Meta 2 (not meta_base)
            if tipo == "Calçado" and metas_calc and "calcado" in metas_calc:
                meta_final = metas_calc["calcado"].get("meta_2") or metas_calc["calcado"].get("meta_base", 0)
            elif tipo == "Roupa" and metas_calc and "roupa" in metas_calc:
                meta_final = metas_calc["roupa"].get("meta_2") or metas_calc["roupa"].get("meta_base", 0)
            elif tipo == "Loja" and metas_calc and "loja" in metas_calc:
                meta_final = metas_calc["loja"].get("meta_2") or metas_calc["loja"].get("meta_base", 0)
            else:
                meta_final = 0

            try:
                meta_final = float(meta_final)
            except (TypeError, ValueError):
                meta_final = 0.0

            meta_proporcional = meta_final * proporcao if dia_atual and meta_final > 0 else meta_final

            vendedores_data.append({
                "cod_vendedor": cod_vendedor,
                "nom_vendedor": nom_vendedor,
                "tipo": tipo,
                "vlr_atual": round(vlr_atual, 2),
                "meta_final": round(meta_final, 2),
                "meta_proporcional": round(meta_proporcional, 2),
                "percentual": round((vlr_atual / meta_final * 100), 1) if meta_final > 0 else 0
            })

        # Sort by vendas atuais descending
        vendedores_data.sort(key=lambda x: x["vlr_atual"], reverse=True)

        return {
            "ano": ano,
            "mes": mes,
            "dia_atual": dia_atual,
            "dias_no_mes": dias_no_mes,
            "proporcao": proporcao,
            "vendedores": vendedores_data,
            "metas_calculadas": metas_calc
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting metas atual for {ano}/{mes}: {str(e)}", exc_info=True)
        # Return empty structure instead of 500 error to prevent frontend crashes
        try:
            hoje = date.today()
            dia_atual = hoje.day if hoje.year == ano and hoje.month == mes else None
        except:
            dia_atual = None
        return {
            "ano": ano,
            "mes": mes,
            "dia_atual": dia_atual,
            "dias_no_mes": 31,
            "proporcao": 0,
            "vendedores": [],
            "metas_calculadas": None,
            "error": str(e)
        }


@router.get("/api/metas/vendedor/{cod_vendedor}/progresso/{ano}/{mes}")
async def get_vendedor_progresso(cod_vendedor: int, ano: int, mes: int):
    """
    Get daily sales progress for a seller in the selected month.
    Returns daily cumulative sales, proportional targets, and final target.
    """
    try:
        from datetime import date, timedelta
        import calendar
        
        # Calculate date range for the month
        data_ini = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano, mes + 1, 1) - timedelta(days=1)
        
        dias_no_mes = data_fim.day
        hoje = date.today()
        dia_atual = hoje.day if hoje.year == ano and hoje.month == mes else dias_no_mes
        
        # Get seller info and tipo
        all_vendedores_info = VendedorPostgres.get_vendedores_ativos()
        vendedor_info = next((v for v in all_vendedores_info if v.get('cod_vendedor') == cod_vendedor), None)
        nom_vendedor = vendedor_info.get('nom_vendedor') if vendedor_info else f"Vendedor {cod_vendedor}"
        
        # Get config to determine tipo and target
        config = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        
        tipo = "Calçado"  # Default
        meta_final = 0.0
        meta_1_value = 0.0
        meta_2_value = 0.0
        
        if config:
            vendedores_tipo = getattr(config, 'vendedores_tipo', None) or []
            tipo_info = next(
                (vt for vt in vendedores_tipo if getattr(vt, 'cod_vendedor', None) == cod_vendedor),
                None
            )
            if tipo_info:
                tipo = getattr(tipo_info, 'tipo', 'Calçado')
            
            # Get calculated metas to find the target
            try:
                metas_calc = await _calcular_metas_internal(ano, mes, config)
                if metas_calc:
                    await _apply_saved_metas_overrides(metas_calc, ano, mes)
                if tipo == "Calçado" and metas_calc and "calcado" in metas_calc:
                    meta_final = metas_calc["calcado"].get("meta_base", 0)
                    meta_1_value = metas_calc["calcado"].get("meta_1", 0)
                    meta_2_value = metas_calc["calcado"].get("meta_2", 0)
                    # Try to get per-seller meta if available
                    calcado_detalhes = metas_calc["calcado"].get("vendedores_detalhes", [])
                    seller_detail = next((d for d in calcado_detalhes if d.get('cod_vendedor') == cod_vendedor), None)
                    if seller_detail:
                        meta_1_value = seller_detail.get('meta_1', meta_1_value)
                        meta_2_value = seller_detail.get('meta_2', meta_2_value)
                elif tipo == "Roupa" and metas_calc and "roupa" in metas_calc:
                    meta_final = metas_calc["roupa"].get("meta_base", 0)
                    meta_1_value = metas_calc["roupa"].get("meta_1", 0)
                    meta_2_value = metas_calc["roupa"].get("meta_2", 0)
                    # Try to get per-seller meta if available
                    roupa_detalhes = metas_calc["roupa"].get("vendedores_detalhes", [])
                    seller_detail = next((d for d in roupa_detalhes if d.get('cod_vendedor') == cod_vendedor), None)
                    if seller_detail:
                        meta_1_value = seller_detail.get('meta_1', meta_1_value)
                        meta_2_value = seller_detail.get('meta_2', meta_2_value)
            except Exception as e:
                logger.warning(f"Error getting metas for progresso: {str(e)}")
        
        # Get daily sales data
        dias = []
        vendas_cumulativas = []
        meta_proporcional_diaria = []
        meta_1_diaria = []
        meta_2_diaria = []
        
        vendas_acumuladas = 0.0
        
        for dia in range(1, dia_atual + 1):
            data_dia = date(ano, mes, dia)
            
            # Get sales for this day
            try:
                sales = VendedorPostgres.get_vendas_by_day(
                    cod_vendedor,
                    data_dia.strftime("%Y-%m-%d"),
                    data_dia.strftime("%Y-%m-%d")
                )
                vlr_dia = sum(float(s.get('vlr_liquido_total', 0)) for s in sales) if sales else 0.0
                vendas_acumuladas += vlr_dia
            except Exception as e:
                logger.warning(f"Error getting sales for day {dia}: {str(e)}")
                vlr_dia = 0.0
            
            # Calculate proportional target for this day
            proporcao_dia = dia / dias_no_mes
            meta_proporcional = meta_final * proporcao_dia
            meta_1_prop = meta_1_value * proporcao_dia
            meta_2_prop = meta_2_value * proporcao_dia
            
            dias.append(dia)
            vendas_cumulativas.append(vendas_acumuladas)
            meta_proporcional_diaria.append(meta_proporcional)
            meta_1_diaria.append(meta_1_prop)
            meta_2_diaria.append(meta_2_prop)
        
        return {
            "cod_vendedor": cod_vendedor,
            "nom_vendedor": nom_vendedor,
            "tipo": tipo,
            "ano": ano,
            "mes": mes,
            "dia_atual": dia_atual,
            "dias_no_mes": dias_no_mes,
            "meta_final": meta_final,
            "meta_1": meta_1_value,
            "meta_2": meta_2_value,
            "vendas_atual": vendas_acumuladas,
            "meta_proporcional_atual": meta_final * (dia_atual / dias_no_mes) if dia_atual > 0 else 0,
            "dias": dias,
            "vendas_cumulativas": vendas_cumulativas,
            "meta_proporcional_diaria": meta_proporcional_diaria,
            "meta_1_diaria": meta_1_diaria,
            "meta_2_diaria": meta_2_diaria
        }
    except Exception as e:
        logger.error(f"Error getting vendedor progresso: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/metas/verificar-vendas/{ano}/{mes}")
async def verificar_vendas_ano_anterior(ano: int, mes: int):
    """
    Verify sales data from previous year for debugging.
    Returns detailed breakdown of what sales data is available.
    """
    try:
        ano_anterior = ano - 1
        
        # Calculate date range
        from datetime import date, timedelta
        data_ini = date(ano_anterior, mes, 1)
        if mes == 12:
            data_fim = date(ano_anterior + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano_anterior, mes + 1, 1) - timedelta(days=1)
        
        # Get all vendedores
        all_vendedores = VendedorPostgres.get_vendedores_ativos()
        
        # Get config to determine tipos
        config = await engine.find_one(
            VendedorConfigMetas,
            (VendedorConfigMetas.ano == ano) & (VendedorConfigMetas.mes == mes)
        )
        vendedores_tipo_dict = {}
        if config:
            vendedores_tipo = getattr(config, 'vendedores_tipo', None) or []
            for vt in vendedores_tipo:
                cod_vend = getattr(vt, 'cod_vendedor', None)
                tipo_vend = getattr(vt, 'tipo', None)
                if cod_vend and tipo_vend:
                    vendedores_tipo_dict[cod_vend] = tipo_vend
        
        # Get sales for each vendedor - show ALL vendedores with sales, not just those with tipo configured
        vendas_detalhadas = []
        total_vendas = 0.0
        vendedores_com_vendas_set = set()
        
        # First, find all vendedores with sales
        for vendedor in all_vendedores:
            cod_vendedor = vendedor.get('cod_vendedor')
            if not cod_vendedor:
                continue
            
            try:
                sales = VendedorPostgres.get_vendas_monthly_summary(cod_vendedor, ano_anterior)
                if sales and isinstance(sales, list):
                    for sale in sales:
                        sale_mes = sale.get('mes')
                        sale_mes_int = int(sale_mes) if sale_mes is not None else None
                        if sale_mes_int == mes:
                            vendedores_com_vendas_set.add(cod_vendedor)
                            break
            except Exception as e:
                logger.debug(f"Error checking sales for vendedor {cod_vendedor}: {str(e)}")
                continue
        
        # Now process all vendedores with sales
        for cod_vendedor in vendedores_com_vendas_set:
            try:
                # Get tipo from config, default to "Calçado" if not in Calçado or Roupa
                tipo = vendedores_tipo_dict.get(cod_vendedor, "Calçado")
                
                # Get vendedor name
                vendedor_info = next((v for v in all_vendedores if v.get('cod_vendedor') == cod_vendedor), None)
                nom_vendedor = vendedor_info.get('nom_vendedor') if vendedor_info else f"Vendedor {cod_vendedor}"
                
                # Get monthly summary
                sales = VendedorPostgres.get_vendas_monthly_summary(cod_vendedor, ano_anterior)
                vendedor_sales = 0.0
                
                if sales and isinstance(sales, list):
                    for sale in sales:
                        sale_mes = sale.get('mes')
                        sale_mes_int = int(sale_mes) if sale_mes is not None else None
                        if sale_mes_int == mes:
                            vlr = sale.get('vlr_liquido_total', 0)
                            try:
                                vendedor_sales += float(vlr) if vlr else 0.0
                            except (ValueError, TypeError):
                                pass
                
                # Also try direct date range query
                try:
                    direct_sales = VendedorPostgres.get_vendas_by_day(
                        cod_vendedor,
                        data_ini.strftime("%Y-%m-%d"),
                        data_fim.strftime("%Y-%m-%d")
                    )
                    direct_total = sum(float(s.get('vlr_liquido_total', 0)) for s in direct_sales) if direct_sales else 0.0
                except:
                    direct_total = 0.0
                
                if vendedor_sales > 0 or direct_total > 0:
                    vendas_detalhadas.append({
                        "cod_vendedor": cod_vendedor,
                        "nom_vendedor": nom_vendedor,
                        "tipo": tipo,
                        "vlr_monthly_summary": vendedor_sales,
                        "vlr_direct_query": direct_total,
                        "diferenca": abs(vendedor_sales - direct_total)
                    })
                    total_vendas += max(vendedor_sales, direct_total)
            except Exception as e:
                logger.warning(f"Error checking sales for vendedor {cod_vendedor}: {str(e)}")
                continue
        
        return {
            "ano_anterior": ano_anterior,
            "mes": mes,
            "data_ini": data_ini.strftime("%Y-%m-%d"),
            "data_fim": data_fim.strftime("%Y-%m-%d"),
            "total_vendedores_verificados": len(all_vendedores),
            "vendedores_com_vendas": len(vendas_detalhadas),
            "total_vendas": total_vendas,
            "vendas_detalhadas": vendas_detalhadas,
            "fonte": "COMISSAO.base_calc_comissao (fonte única de verdade - já exclui cancelados e devoluções)"
        }
    except Exception as e:
        logger.error(f"Error verifying sales: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
