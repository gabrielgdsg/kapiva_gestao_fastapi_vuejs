# from flask import Blueprint, request, jsonify
from fastapi import APIRouter, Request, HTTPException
from ..models.financeiro_caixa import Caixa, LojSangria, LojTroco, LojSuprimento, LojCartao, SistDinheiro, SistPos, SistTroco, SistTotal, ResCaixa, User
from .caixa_postgres import CaixaPostgres
from db_mongo.database import engine
from decimal import Decimal
from datetime import date, datetime
import requests
import untangle
from fastapi.encoders import jsonable_encoder
from openpyxl import load_workbook
import logging

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/financeiro/caixa/debug-paf-schema")
async def debug_paf_caixa_schema():
    """Discover PAF_CAIXA columns and sample operador mapping. Useful when nom_operador is empty."""
    from app.db_postgres.connection import CursorFromConnectionFromPool
    out = {"columns": [], "sample": [], "operador_map": None}
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE LOWER(table_name) = 'paf_caixa' 
                ORDER BY ordinal_position
            """)
            out["columns"] = [{"name": r[0], "type": r[1]} for r in cursor.fetchall()]
            try:
                cursor.execute("SELECT * FROM PAF_CAIXA ORDER BY DATA_CAIXA DESC LIMIT 3")
            except Exception:
                cursor.execute("SELECT * FROM paf_caixa ORDER BY data_caixa DESC LIMIT 3")
            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
            sample_date = None
            date_col = next((c for c in cols if c and 'data' in c.lower() and 'caixa' in c.lower()), None) or 'data_caixa'
            for row in rows:
                d = dict(zip(cols, row))
                v = d.get(date_col) or d.get('DATA_CAIXA') or d.get('data_caixa')
                if v:
                    sample_date = v.strftime("%Y-%m-%d") if hasattr(v, 'strftime') else str(v)[:10]
                    break
            def _serialize(v):
                if hasattr(v, 'strftime'): return v.strftime('%Y-%m-%d %H:%M:%S')
                if hasattr(v, 'isoformat'): return v.isoformat()
                return v
            out["sample"] = [{k: _serialize(v) for k, v in dict(zip(cols, row)).items()} for row in rows]
            if sample_date:
                out["operador_map"] = CaixaPostgres._get_caixa_operador_map(cursor, sample_date)
    except Exception as e:
        out["error"] = str(e)
    return out


def _raw_to_caixa_dict(data_caixa_datetime, caixa_loaded, cod_caixa=None):
    """Convert raw DB output to Caixa-like dict for API response."""
    loj_sangria_list = [{"item": "Sangria " + str(idx + 1), "valor": float(v)} for idx, v in enumerate(caixa_loaded[0])]
    loj_suprimento_val = caixa_loaded[1][0] if caixa_loaded[1] else 0
    return {
        "data_caixa": data_caixa_datetime.isoformat() if hasattr(data_caixa_datetime, 'isoformat') else str(data_caixa_datetime),
        "cod_caixa": cod_caixa,
        "loj_sangria_list": loj_sangria_list,
        "loj_outras_entradas_list": [],
        "loj_suprimento": {"item": "Suprimento", "valor": float(loj_suprimento_val)},
        "loj_cartao": {"item": "Cartao", "valor": 0},
        "loj_troco": {"item": "Troco", "valor": 0},
        "loj_total": {"item": "TOTAL Loja", "valor": 0},
        "sist_troco": {"item": "Troco", "valor": float(caixa_loaded[2][0] if caixa_loaded[2] else 0)},
        "sist_pos": {"item": "P.O.S.", "valor": float(caixa_loaded[3][0] if caixa_loaded[3] else 0)},
        "sist_dinheiro": {"item": "Dinheiro", "valor": float(caixa_loaded[4][0] if caixa_loaded[4] else 0)},
        "sist_total": {"item": "TOTAL Sistema", "valor": 0},
        "res_caixa": {"item": "RESULTADO", "valor": 0},
    }


@router.get("/api/financeiro/caixas/{data_caixa}")
async def get_caixas_table(data_caixa: str):
    """
    Return all caixas for a date (supports 1, 3, or more caixas).
    Returns {caixas: [{cod_caixa: 1, ...}, ...]}.
    """
    try:
        data_caixa_dt = datetime.fromisoformat(data_caixa.replace('Z', '+00:00')[:10])
    except Exception:
        data_caixa_dt = datetime.strptime(data_caixa[:10], '%Y-%m-%d')
    raw_list = CaixaPostgres.load_caixas_from_db(data_caixa)
    if not raw_list:
        # Fallback to legacy single-caixa aggregate
        caixa_loaded = CaixaPostgres.load_caixa_from_db(data_caixa)
        single = _raw_to_caixa_dict(data_caixa_dt, caixa_loaded, cod_caixa=1)
        return {"caixas": [single], "total_caixas": 1}
    caixas = []
    for r in raw_list:
        loj_sangria_list = [{"item": "Sangria " + str(i + 1), "valor": float(v)} for i, v in enumerate(r.get("loj_sangria", []) or [])]
        loj_suprimento_val = float(r.get("loj_suprimento") or 0)
        sist_troco_val = float(r.get("sist_troco") or 0)
        sist_pos_val = float(r.get("sist_pos") or 0)
        sist_dinheiro_val = float(r.get("sist_dinheiro") or 0)
        sist_total_val = sist_dinheiro_val + sist_pos_val + sist_troco_val
        caixas.append({
            "data_caixa": data_caixa,
            "cod_caixa": r.get("cod_caixa"),
            "nom_operador": r.get("nom_operador"),
            "loj_sangria_list": loj_sangria_list,
            "loj_outras_entradas_list": [],
            "loj_suprimento": {"item": "Suprimento", "valor": loj_suprimento_val},
            "loj_cartao": {"item": "Cartao", "valor": 0},
            "loj_troco": {"item": "Troco", "valor": 0},
            "loj_total": {"item": "TOTAL Loja", "valor": 0},
            "sist_troco": {"item": "Troco", "valor": sist_troco_val},
            "sist_pos": {"item": "P.O.S.", "valor": sist_pos_val},
            "sist_dinheiro": {"item": "Dinheiro", "valor": sist_dinheiro_val},
            "sist_total": {"item": "TOTAL Sistema", "valor": sist_total_val},
            "res_caixa": {"item": "RESULTADO", "valor": 0},
        })
    return {"caixas": caixas, "total_caixas": len(caixas)}


@router.get("/api/financeiro/caixa/{data_caixa}")
async def get_caixa_table(data_caixa: str):
    data_caixa_datetime = datetime.fromisoformat(data_caixa.replace('Z', '+00:00')[:10]) if 'T' in data_caixa else datetime.strptime(data_caixa[:10], '%Y-%m-%d')
    caixa = await engine.find_one(Caixa, Caixa.data_caixa == data_caixa_datetime)
    if caixa is None:
        raw_list = CaixaPostgres.load_caixas_from_db(data_caixa)
        if raw_list:
            # Use first caixa for backward compatibility
            r = raw_list[0]
            loj_sangria_list = [LojSangria(item="Sangria " + str(i + 1), valor=Decimal(str(v))) for i, v in enumerate(r.get("loj_sangria", []) or [])]
            loj_suprimento = LojSuprimento(item="Suprimento", valor=Decimal(str(r.get("loj_suprimento") or 0)))
            sist_troco = SistTroco(item="Troco", valor=Decimal(str(r.get("sist_troco") or 0)))
            sist_pos = SistPos(item="P.O.S.", valor=Decimal(str(r.get("sist_pos") or 0)))
            sist_dinheiro = SistDinheiro(item="Dinheiro", valor=Decimal(str(r.get("sist_dinheiro") or 0)))
            caixa = Caixa(
                data_caixa=data_caixa_datetime,
                loj_sangria_list=loj_sangria_list,
                loj_outras_entradas_list=[],
                loj_suprimento=loj_suprimento,
                loj_cartao=LojCartao(item="Cartao", valor=Decimal(0)),
                loj_troco=LojTroco(item="Troco", valor=Decimal(0)),
                loj_total=LojTroco(item="TOTAL Loja", valor=Decimal(0)),
                sist_troco=sist_troco,
                sist_pos=sist_pos,
                sist_dinheiro=sist_dinheiro,
                sist_total=SistTotal(item="TOTAL Sistema", valor=Decimal(0)),
                res_caixa=ResCaixa(item="RESULTADO", valor=Decimal(0)),
            )
        else:
            caixa_loaded = CaixaPostgres.load_caixa_from_db(data_caixa)
            loj_sangria_list = []
            for idx, val in enumerate(caixa_loaded[0]):
                sangria = LojSangria(item="Sangria "+str(idx+1), valor=val)
                loj_sangria_list.append(sangria)
            loj_outras_entradas_list = []
            loj_suprimento = LojSuprimento(item="Suprimento", valor=caixa_loaded[1][0])
            loj_cartao = LojCartao(item="Cartao", valor=Decimal(0))
            loj_troco = LojTroco(item="Troco", valor=Decimal(0))
            loj_total = LojTroco(item="TOTAL Loja", valor=Decimal(0))
            sist_troco = SistTroco(item="Troco", valor=caixa_loaded[2][0])
            sist_pos = SistPos(item="P.O.S.", valor=caixa_loaded[3][0])
            sist_dinheiro = SistDinheiro(item="Dinheiro", valor=caixa_loaded[4][0])
            res_caixa = ResCaixa(item="RESULTADO", valor=Decimal(0))
            sist_total = SistTotal(item="TOTAL Sistema", valor=Decimal(0))
            caixa = Caixa(data_caixa=data_caixa_datetime, loj_sangria_list=loj_sangria_list,
                          loj_outras_entradas_list=loj_outras_entradas_list, loj_suprimento=loj_suprimento, loj_cartao=loj_cartao, loj_troco=loj_troco, loj_total=loj_total, sist_troco=sist_troco,
                          sist_pos=sist_pos, sist_dinheiro=sist_dinheiro, sist_total=sist_total, res_caixa=res_caixa)
    return jsonable_encoder(caixa)


@router.put("/api/financeiro/caixa/save_to_db")
async def update_caixa_table_user(caixa_put: Caixa):
    caixa = await engine.find_one(Caixa, Caixa.data_caixa == caixa_put.data_caixa)
    if caixa is not None:
        # Creating a new instansce of caixa with 'id' from the existant one
        caixa_updated = Caixa(**{**caixa_put.dict(), "id": caixa.id})
        await engine.save(caixa_updated)
    else:
        await engine.save(caixa_put)
    return "db_updated"


@router.put("/api/financeiro/caixa/save_to_excel")
async def save_caixa_to_file(caixa: Caixa):
    workbook_name = 'caixa.xlsx'
    wb = load_workbook(workbook_name)
    page = wb.active
    table = []
    table.append([caixa.data_caixa.strftime("%d/%m/%Y")])
    for element in caixa.loj_sangria_list:
        line = [element.item, float(str(element.valor))]
        table.append(line)
    for element in caixa.loj_outras_entradas_list:
        line = [element.item, float(str(element.valor))]
        table.append(line)
    table.append([caixa.loj_cartao.item, float(str(caixa.loj_cartao.valor))])
    table.append([caixa.loj_suprimento.item, float(str(caixa.loj_suprimento.valor))])
    table.append([caixa.loj_troco.item, float(str(caixa.loj_troco.valor))])
    table.append([caixa.loj_total.item, float(str(caixa.loj_total.valor)), caixa.res_caixa.item, float(str(caixa.res_caixa.valor))])

    table[1][2:2] = [caixa.sist_dinheiro.item, float(str(caixa.sist_dinheiro.valor))] # insert at position 2 from list
    table[2][2:2] = [caixa.sist_pos.item, float(str(caixa.sist_pos.valor))]
    table[3][2:2] = [caixa.sist_troco.item, float(str(caixa.sist_troco.valor))]
    table[4][2:2] = [caixa.sist_total.item, float(str(caixa.sist_total.valor))]
    # table[1].append(caixa.sist_dinheiro.item)
    # table[1].append(float(str(caixa.sist_dinheiro.valor)))
    # table[2].append(caixa.sist_pos.item)
    # table[2].append(float(str(caixa.sist_pos.valor)))
    # table[3].append(caixa.sist_troco.item)
    # table[3].append(float(str(caixa.sist_troco.valor)))
    # table[4].append(caixa.sist_total.item)
    # table[4].append(float(str(caixa.sist_total.valor)))

    for line in table:
        page.append(line)

    # for element in caixa.loj_sangria_list:
    #     line = [element.item, float(str(element.valor))]
    #     page.append(line)
    # for element in caixa.loj_outras_entradas_list:
    #     line = [element.item, float(str(element.valor))]
    #     page.append(line)
    # page.append([caixa.loj_cartao.item, float(str(caixa.loj_cartao.valor))])
    # print('entered')
    # page.append([''])
    # page.append(caixa.data_caixa)
    # for i in caixa:
    #     if i[0] == 'id':
    #         print(i[0])
    #     elif i[0] == 'data_caixa':
    #         page.append([i[1].strftime("%d/%m/%Y")])
    #
    #     elif isinstance(i[1], list):
    #         for j in i[1]:
    #             line = [j.item, float(str(j.valor))]
    #             page.append(line)
    #     else:
    #         line = [i[1].item, float(str(i[1].valor))]
    #         page.append(line)
    page.append([''])
    wb.save(filename=workbook_name)
    return "saved to excel"


@router.get("/api/financeiro/caixacartao/{data_caixa}")
async def cartao(data_caixa: str, request: Request):
    """Get credit card sales data for a specific date (Stone + Sicredi Máquinas)."""
    try:
        data_dt = datetime.strptime(data_caixa[:10], '%Y-%m-%d').date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format")
    result = get_cartao_vendas(data_dt)
    return {
        "loj_cartao": str(result["total"]),
        "stone": result.get("stone", 0),
        "sicredi": result.get("sicredi", 0),
        "sources": result.get("sources", [])
    }


def _get_stone_cartao(data_caixa_date) -> Decimal:
    """Fetch Stone conciliation. Uses env vars or legacy hardcoded fallback."""
    ref = data_caixa_date.strftime("%Y%m%d")
    aff = getattr(settings, "STONE_AFFILIATION_CODE", None) or "232084871"
    token = getattr(settings, "STONE_BEARER_TOKEN", None) or "7b5fd261-3537-4a8a-bffc-0f2d5ec34501"
    auth_raw = getattr(settings, "STONE_AUTH_RAW", None) or "kapivacalcados2020emmovimento"
    auth_enc = getattr(settings, "STONE_AUTH_ENCRYPTED", None) or "084da7241e06fa5612edf44693991cb5b1af63e118cf5fdaa27a1faaa866f04162eee459d7536bcdf00ff80e512aa3ad1d9f408b64d3a06b94791d484de09c95"
    url = f"https://conciliation.stone.com.br/conciliation-file/v2.2/{ref}"
    headers = {
        "authorization": f"Bearer {token}",
        "x-authorization-raw-data": auth_raw,
        "x-authorization-encrypted-data": auth_enc,
        "accept-encoding": "gzip"
    }
    try:
        r = requests.get(url, headers=headers, params={"affiliationCode": aff}, timeout=30)
        if r.status_code != 200:
            return Decimal(0)
        obj = untangle.parse(r.text)
        total = Decimal(0)
        if hasattr(obj, "Conciliation") and hasattr(obj.Conciliation, "FinancialTransactions"):
            txs = obj.Conciliation.FinancialTransactions
            if hasattr(txs, "Transaction"):
                for t in (txs.Transaction if isinstance(txs.Transaction, list) else [txs.Transaction]):
                    if hasattr(t, "CapturedAmount") and t.CapturedAmount and t.CapturedAmount.cdata:
                        total += Decimal(str(t.CapturedAmount.cdata))
        return total
    except Exception as e:
        logger.warning("Stone cartao fetch failed: %s", e)
        return Decimal(0)


def _get_sicredi_cartao(data_caixa_date) -> Decimal:
    """Fetch Sicredi Máquinas conciliation. Configure via SICREDI_* env vars."""
    url = getattr(settings, "SICREDI_API_URL", None) or ""
    token = getattr(settings, "SICREDI_API_TOKEN", None) or ""
    if not url or not token:
        return Decimal(0)
    ref = data_caixa_date.strftime("%Y-%m-%d")
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params={"data": ref, "estabelecimento": getattr(settings, "SICREDI_ESTABELECIMENTO_ID", "")},
            timeout=30
        )
        if r.status_code != 200:
            return Decimal(0)
        data = r.json()
        total = Decimal(0)
        if isinstance(data, dict) and "valor" in data:
            total = Decimal(str(data["valor"]))
        elif isinstance(data, dict) and "transacoes" in data:
            for t in data["transacoes"]:
                total += Decimal(str(t.get("valor", 0) or 0))
        elif isinstance(data, list):
            for t in data:
                total += Decimal(str(t.get("valor", 0) or 0))
        return total
    except Exception as e:
        logger.warning("Sicredi cartao fetch failed: %s", e)
        return Decimal(0)


def get_cartao_vendas(data_caixa_date):
    """Aggregate cartão from Stone + Sicredi. Returns {total, stone, sicredi, sources}."""
    stone_val = _get_stone_cartao(data_caixa_date)
    sicredi_val = _get_sicredi_cartao(data_caixa_date)
    total = stone_val + sicredi_val
    sources = []
    if stone_val > 0:
        sources.append("Stone")
    if sicredi_val > 0:
        sources.append("Sicredi")
    return {
        "total": total,
        "stone": float(stone_val),
        "sicredi": float(sicredi_val),
        "sources": sources
    }
