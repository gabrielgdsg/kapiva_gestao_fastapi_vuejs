"""
API routes for Clientes dashboard.
PostgreSQL (read-only): cliente, receber, nota_fiscal
MongoDB: scores, write-offs, campanha config
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging

from .clientes_postgres import ClientesPostgres
from .clientes_models import ClienteScore, ClienteWriteoff, CampanhaConfig
from db_mongo.database import engine

logger = logging.getLogger(__name__)
router = APIRouter()


def _calcular_score(data: dict) -> tuple:
    score = 40
    vencidas = int(data.get("parcelas_vencidas") or 0)
    mediana = float(data.get("mediana_dias_atraso") or 0)
    recompra = bool(data.get("recompra_pos_quita"))
    total = int(data.get("total_parcelas") or 0)
    if vencidas == 0:
        score += 20
    else:
        score -= min(vencidas * 10, 30)
    if mediana == 0:
        score += 15
    elif mediana > 90:
        score -= 30
    elif mediana > 30:
        score -= 20
    if recompra:
        score += 10
    if total >= 6:
        score += 5
    score = max(0, min(100, score))
    grade = "A" if score >= 75 else "B" if score >= 50 else "C" if score >= 25 else "D"
    return score, grade


def _calcular_tags(data: dict, score: int, vlr_aberto: float, total_gasto: float) -> List[str]:
    tags = []
    vencidas = int(data.get("parcelas_vencidas") or 0)
    pagas = int(data.get("parcelas_pagas") or 0)
    if vencidas > 0 and pagas == 0:
        tags.append("Perdido")
    elif vencidas > 0:
        tags.append("Em Atraso")
    else:
        tags.append("Adimplente")
    if total_gasto >= 3000:
        tags.append("VIP")
    return tags


@router.get("/api/clientes/kpis")
async def get_kpis():
    try:
        return ClientesPostgres.get_kpis_gerais()
    except Exception as e:
        logger.error(f"Error in get_kpis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar KPIs")


@router.get("/api/clientes/inadimplencia-historico")
async def get_inadimplencia_historico(meses: int = Query(24, ge=1, le=72)):
    try:
        return ClientesPostgres.get_inadimplencia_historico(meses=meses)
    except Exception as e:
        logger.error(f"Error in get_inadimplencia_historico: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico")


@router.get("/api/clientes/devedores-por-mes")
async def get_devedores_por_mes(
    period: str = Query(..., description="YYYY-MM for month, e.g. 2024-03"),
    limit: int = Query(50, ge=1, le=200),
):
    """Clients with overdue in a specific month, ordered by vlr_vencido desc."""
    try:
        return ClientesPostgres.get_devedores_por_periodo(period=period, limit=limit)
    except Exception as e:
        logger.error(f"Error in get_devedores_por_mes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar devedores do mês")


@router.get("/api/clientes/top-devedores")
async def get_top_devedores(limit: int = Query(10, ge=1, le=50)):
    try:
        return ClientesPostgres.get_top_devedores(limit=limit)
    except Exception as e:
        logger.error(f"Error in get_top_devedores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar top devedores")


@router.get("/api/clientes/distribuicao-parcelas")
async def get_distribuicao_parcelas(meses: int = Query(12, ge=1, le=24)):
    try:
        return ClientesPostgres.get_distribuicao_parcelas(meses=meses)
    except Exception as e:
        logger.error(f"Error in get_distribuicao_parcelas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar distribuição")


@router.get("/api/clientes/aniversariantes")
async def get_aniversariantes(mes: Optional[int] = Query(None, ge=1, le=12)):
    try:
        return ClientesPostgres.get_aniversariantes_mes(mes=mes)
    except Exception as e:
        logger.error(f"Error in get_aniversariantes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar aniversariantes")


@router.get("/api/clientes/vip")
async def get_clientes_vip(
    limit: int = Query(20, ge=1, le=100),
    range_type: Optional[str] = Query("all", description="all, this_year, last_year, last_2_years"),
):
    try:
        return ClientesPostgres.get_clientes_vip(limit=limit, range_type=range_type)
    except Exception as e:
        logger.error(f"Error in get_clientes_vip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar VIP")


@router.get("/api/clientes/writeoffs")
async def get_writeoffs():
    try:
        summary = ClientesPostgres.get_writeoffs_postgres()
        clientes = ClientesPostgres.get_writeoff_clientes()
        mongo_writeoffs = await engine.find(ClienteWriteoff, ClienteWriteoff.ativo == True)
        mongo_set = {w.cod_cliente for w in mongo_writeoffs}
        for c in clientes:
            c["writeoff_manual"] = c["cod_cliente"] in mongo_set
        net = float(summary.get("total_juros_recebidos_geral", 0)) - float(summary.get("total_perdido", 0) or 0)
        return {"summary": summary, "net_balance": net, "clientes": clientes}
    except Exception as e:
        logger.error(f"Error in get_writeoffs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar baixas de crédito")


@router.post("/api/clientes/{cod_cliente}/writeoff")
async def registrar_writeoff(
    cod_cliente: int,
    motivo: Optional[str] = Query(None),
    registrado_por: Optional[str] = Query(None),
):
    try:
        cliente = ClientesPostgres.get_cliente_detalhe(cod_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        receber = ClientesPostgres.get_cliente_receber(cod_cliente, apenas_aberto=True)
        vlr_perdido = sum(float(r.get("vlr_saldo", 0) or 0) for r in receber)
        existing = await engine.find_one(ClienteWriteoff, ClienteWriteoff.cod_cliente == cod_cliente)
        if existing:
            existing.ativo = True
            existing.motivo = motivo
            existing.registrado_em = datetime.utcnow()
            existing.registrado_por = registrado_por
            await engine.save(existing)
            return {"message": "Write-off atualizado", "cod_cliente": cod_cliente}
        w = ClienteWriteoff(cod_cliente=cod_cliente, nom_cliente=str(cliente.get("nom_cliente", "")),
            vlr_perdido=vlr_perdido, motivo=motivo, registrado_por=registrado_por)
        await engine.save(w)
        return {"message": "Write-off registrado", "cod_cliente": cod_cliente}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in registrar_writeoff: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao registrar baixa de crédito")


@router.get("/api/clientes/lista")
async def get_clientes_lista(
    search: Optional[str] = Query(None),
    apenas_ativos: bool = Query(True),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    try:
        return ClientesPostgres.get_clientes_lista(search=search, apenas_ativos=apenas_ativos, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Error in get_clientes_lista: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar lista")


@router.get("/api/clientes/{cod_cliente}")
async def get_cliente(cod_cliente: int):
    try:
        cliente = ClientesPostgres.get_cliente_detalhe(cod_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        compras = ClientesPostgres.get_cliente_compras(cod_cliente, limit=20)
        parcelas = ClientesPostgres.get_cliente_receber(cod_cliente)
        cached = await engine.find_one(ClienteScore, ClienteScore.cod_cliente == cod_cliente)
        if cached:
            score_data = {"score": cached.score, "grade": cached.grade, "tags": cached.tags,
                "mediana_dias_atraso": cached.mediana_dias_atraso, "total_juros_pagos": cached.total_juros_pagos,
                "recompra_pos_quita": cached.recompra_pos_quita, "calculado_em": cached.calculado_em}
        else:
            raw = ClientesPostgres.get_cliente_score_data(cod_cliente)
            total_gasto = sum(float(c.get("vlr_total", 0) or 0) for c in compras)
            vlr_aberto = sum(float(p.get("vlr_saldo", 0) or 0) for p in parcelas if p.get("flg_aberto") == "S")
            score, grade = _calcular_score(raw)
            tags = _calcular_tags(raw, score, vlr_aberto, total_gasto)
            score_data = {"score": score, "grade": grade, "tags": tags,
                "mediana_dias_atraso": float(raw.get("mediana_dias_atraso") or 0),
                "total_juros_pagos": float(raw.get("total_juros_pagos") or 0),
                "recompra_pos_quita": bool(raw.get("recompra_pos_quita")), "calculado_em": None}
        vlr_aberto = sum(float(p.get("vlr_saldo", 0) or 0) for p in parcelas if p.get("flg_aberto") == "S")
        vlr_vencido = sum(float(p.get("vlr_saldo", 0) or 0) for p in parcelas
            if p.get("flg_aberto") == "S" and (p.get("dias_atraso") or 0) > 0)
        total_gasto = sum(float(c.get("vlr_total", 0) or 0) for c in compras)
        vlr_limite = float(cliente.get("vlr_limite") or 0)
        return {
            "cliente": cliente,
            "score": score_data,
            "compras": compras,
            "parcelas": parcelas,
            "stats": {
                "total_gasto": total_gasto,
                "total_compras": len(compras),
                "ticket_medio": total_gasto / len(compras) if compras else 0,
                "vlr_aberto": vlr_aberto,
                "vlr_vencido": vlr_vencido,
                "vlr_limite": vlr_limite,
                "pct_limite_usado": (vlr_aberto / vlr_limite * 100) if vlr_limite > 0 else 0,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_cliente {cod_cliente}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar cliente")


@router.get("/api/clientes/nf/{nf_interno}/items")
async def get_cliente_nf_items(nf_interno: int):
    """Items (produtos) for a client's invoice. Same as vendedor NF items."""
    try:
        from app.api.vendedor.vendedor_postgres import VendedorPostgres
        return VendedorPostgres.get_vendas_items_by_nf(nf_interno)
    except Exception as e:
        logger.error(f"Error in get_cliente_nf_items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar itens da NF")


@router.get("/api/clientes/campanhas")
async def get_campanhas():
    try:
        campanhas = await engine.find(CampanhaConfig)
        return [{"ano": c.ano, "mes": c.mes, "ativa": c.ativa, "descricao": c.descricao} for c in campanhas]
    except Exception as e:
        logger.error(f"Error in get_campanhas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar campanhas")
