from fastapi import APIRouter, HTTPException, Body
from .comissao_postgres import ComissaoPostgres
from ..models.comissao import ComissaoVendedor, ComissaoDia, ComissaoEditada, ComissaoAlteracaoLog
from db_mongo.database import engine
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from bson import Decimal128
from typing import Optional

router = APIRouter()


@router.get("/api/comissao/{data_ini}/{data_fim}")
async def read_comissao(data_ini: str, data_fim: str):
    # comissao_loaded = ComissaoPostgres.load_comissao_from_db(data_ini, data_fim)
    # return comissao_loaded
    data_ini_datetime = datetime.fromisoformat(data_ini)
    data_fim_datetime = datetime.fromisoformat(data_fim)

    data_current_datetime = data_ini_datetime
    while data_current_datetime <= data_fim_datetime:
        comissao_dia = await engine.find_one(ComissaoDia, ComissaoDia.data_comissao == data_current_datetime)
        if comissao_dia is None:
            data_current_str = data_current_datetime.strftime("%Y-%m-%d")
            comissao_loaded = ComissaoPostgres.load_comissao_from_db(data_current_str, data_current_str)
            comissao_vendedores = []
            for i in range(len(comissao_loaded)):
                # Handle invalid vendedor data: if cod_vendedor is 0 or nom_vendedor is empty/None, set to 'E-commerce'
                cod_vendedor = comissao_loaded[i][0]
                nom_vendedor = comissao_loaded[i][1]
                if cod_vendedor == 0 or not nom_vendedor or nom_vendedor.strip() == '':
                    nom_vendedor = 'E-commerce'
                
                comissao_vendedor = ComissaoVendedor(cod_vendedor=cod_vendedor,
                                                     nom_vendedor=nom_vendedor,
                                                     base_calc_comissao=comissao_loaded[i][2],
                                                     vlr_comissao=comissao_loaded[i][4],
                                                     cred_dev=comissao_loaded[i][3],
                                                     data_ini=datetime.fromisoformat(data_ini),
                                                     data_fim=datetime.fromisoformat(data_fim))
                comissao_vendedores.append(comissao_vendedor)
            nova_comissao_dia = ComissaoDia(data_comissao=data_current_datetime,
                                            comissao_vendedores=comissao_vendedores)
            await update_comissao_dia(nova_comissao_dia)
        data_current_datetime += timedelta(days=1)

    comissao_intervalo = await load_comissao_intervalo_from_db(data_ini_datetime, data_fim_datetime)
    return jsonable_encoder(comissao_intervalo)


async def update_comissao_dia(nova_comissao_dia: ComissaoDia):
    comissao_dia = await engine.find_one(ComissaoDia, ComissaoDia.data_comissao == nova_comissao_dia.data_comissao)
    if comissao_dia is not None:
        # Creating a new instansce of comissao with 'id' from the existant one
        comissao_dia_updated = ComissaoDia(**{**nova_comissao_dia.dict(), "id": comissao_dia.id})
        await engine.save(comissao_dia_updated)
    else:
        await engine.save(nova_comissao_dia)
    return "db_updated"


async def load_comissao_intervalo_from_db(data_ini_datetime: datetime, data_fim_datetime: datetime):
    collection = engine.get_collection(ComissaoDia)
    pipeline = [{'$match': {'data_comissao': {'$gte': data_ini_datetime, '$lte': data_fim_datetime}}},
                {'$unwind': {'path': '$comissao_vendedores'}},
                {'$group': {'_id': '$comissao_vendedores.cod_vendedor',
                            'nom_vendedor': {'$first': '$comissao_vendedores.nom_vendedor'},
                            'base_calc_comissao': {'$sum': '$comissao_vendedores.base_calc_comissao'},
                            'cred_dev': {'$sum': '$comissao_vendedores.cred_dev'},
                            # 'data_ini': {'$first': '$comissao_vendedores.data_ini'},
                            'data_ini': {'$first': data_ini_datetime},
                            # 'data_fim': {'$first': '$comissao_vendedores.data_fim'},
                            'data_fim': {'$first': data_fim_datetime},
                            'vlr_comissao': {'$sum': '$comissao_vendedores.vlr_comissao'}}},
                            #'comissao_total': {'$sum': '$comissao_total'}}},
                {'$sort': {'base_calc_comissao': -1}}]
    documents0 = await collection.aggregate(pipeline).to_list(length=None)


    pipeline.append(
        {'$project': {'_id': 0, 'cod_vendedor': '$_id', 'nom_vendedor': '$nom_vendedor',
                      'base_calc_comissao': '$base_calc_comissao', 'cred_dev': '$cred_dev', 'data_ini': '$data_ini',
                      'data_fim': '$data_fim', 'vlr_comissao': '$vlr_comissao'}}
    )
    documents = await collection.aggregate(pipeline).to_list(length=None)
    comissao_vendedores_list = [ComissaoVendedor.parse_doc(doc) for doc in documents]
    
    # Merge with edited values from MongoDB
    edited_collection = engine.get_collection(ComissaoEditada)
    edited_docs = await edited_collection.find({
        "data_comissao": {"$gte": data_ini_datetime, "$lte": data_fim_datetime}
    }).to_list(length=None)
    
    # Create a map of edited values by cod_vendedor
    edited_map = {}
    for doc in edited_docs:
        cod_vendedor = doc.get('cod_vendedor')
        if cod_vendedor:
            edited_map[cod_vendedor] = doc.get('vlr_comissao_editado')
    
    # Update comissao_vendedores_list with edited values
    for vendedor in comissao_vendedores_list:
        cod_vendedor = vendedor.cod_vendedor if hasattr(vendedor, 'cod_vendedor') else vendedor.get('cod_vendedor')
        if cod_vendedor in edited_map:
            # Replace with edited value
            if hasattr(vendedor, 'vlr_comissao'):
                vendedor.vlr_comissao = edited_map[cod_vendedor]
            else:
                vendedor['vlr_comissao'] = edited_map[cod_vendedor]
    
    comissao_intervalo = ComissaoDia(data_comissao=data_fim_datetime,
                                     comissao_vendedores=comissao_vendedores_list)
    return jsonable_encoder(comissao_intervalo)


@router.delete("/api/comissao/delete/{data_ini}")
async def delete_comissao_dia_from_db(data_ini: str):
    comissao_dia = await engine.find_one(ComissaoDia, ComissaoDia.data_comissao == datetime.fromisoformat(data_ini))
    if comissao_dia is None:
        raise HTTPException(404)
    await engine.delete(comissao_dia)
    return 'comissao_dia deleted'


@router.put("/api/comissao/edit/{data_ini}/{data_fim}")
async def edit_comissao(
    data_ini: str,
    data_fim: str,
    edits: dict = Body(...)
):
    """
    Edit commission values for sellers (MongoDB only, never touches PostgreSQL).
    edits format: {
        "cod_vendedor": {
            "vlr_comissao": new_value,
            "observacao": "optional note"
        }
    }
    """
    try:
        data_ini_datetime = datetime.fromisoformat(data_ini)
        data_fim_datetime = datetime.fromisoformat(data_fim)
        
        # Get original commission data to find original values
        comissao_intervalo = await load_comissao_intervalo_from_db(data_ini_datetime, data_fim_datetime)
        
        # Process each edit
        for cod_vendedor_str, edit_data in edits.items():
            cod_vendedor = int(cod_vendedor_str)
            novo_base_calc = Decimal128(str(edit_data.get('base_calc_comissao', 0)))
            novo_valor_comissao = Decimal128(str(edit_data.get('vlr_comissao', 0)))
            observacao = edit_data.get('observacao', '')
            
            # Find original value from comissao_intervalo
            vendedor_original = next(
                (v for v in comissao_intervalo.get('comissao_vendedores', []) 
                 if v.get('cod_vendedor') == cod_vendedor),
                None
            )
            
            if not vendedor_original:
                continue  # Skip if vendedor not found
            
            base_calc_anterior = vendedor_original.get('base_calc_comissao')
            if isinstance(base_calc_anterior, Decimal128):
                base_calc_anterior_decimal = base_calc_anterior
            else:
                base_calc_anterior_decimal = Decimal128(str(base_calc_anterior)) if base_calc_anterior else Decimal128('0')
            
            valor_anterior = vendedor_original.get('vlr_comissao')
            if isinstance(valor_anterior, Decimal128):
                valor_anterior_decimal = valor_anterior
            else:
                valor_anterior_decimal = Decimal128(str(valor_anterior)) if valor_anterior else Decimal128('0')
            
            # Find or create ComissaoEditada record
            # Use data_fim as the key date for the commission period
            comissao_editada = await engine.find_one(
                ComissaoEditada,
                (ComissaoEditada.data_comissao == data_fim_datetime) & 
                (ComissaoEditada.cod_vendedor == cod_vendedor)
            )
            
            if comissao_editada:
                # Update existing
                base_calc_anterior_atual = getattr(comissao_editada, 'base_calc_comissao_editado', None) or base_calc_anterior_decimal
                valor_anterior_atual = comissao_editada.vlr_comissao_editado
                
                comissao_editada.base_calc_comissao_editado = novo_base_calc
                comissao_editada.vlr_comissao_editado = novo_valor_comissao
                comissao_editada.observacao = observacao
                comissao_editada.data_atualizacao = datetime.now()
                
                # Add log entry
                log_entry = ComissaoAlteracaoLog(
                    data_alteracao=datetime.now(),
                    base_calc_anterior=base_calc_anterior_atual,
                    base_calc_novo=novo_base_calc,
                    valor_anterior=valor_anterior_atual,
                    valor_novo=novo_valor_comissao,
                    observacao=observacao
                )
                comissao_editada.alteracoes.append(log_entry)
            else:
                # Create new
                nom_vendedor = vendedor_original.get('nom_vendedor')
                base_calc = vendedor_original.get('base_calc_comissao')
                cred_dev = vendedor_original.get('cred_dev')
                
                log_entry = ComissaoAlteracaoLog(
                    data_alteracao=datetime.now(),
                    base_calc_anterior=base_calc_anterior_decimal,
                    base_calc_novo=novo_base_calc,
                    valor_anterior=valor_anterior_decimal,
                    valor_novo=novo_valor_comissao,
                    observacao=observacao
                )
                
                comissao_editada = ComissaoEditada(
                    data_comissao=data_fim_datetime,
                    cod_vendedor=cod_vendedor,
                    nom_vendedor=nom_vendedor,
                    base_calc_comissao_original=base_calc_anterior_decimal,
                    base_calc_comissao_editado=novo_base_calc,
                    vlr_comissao_original=valor_anterior_decimal,
                    vlr_comissao_editado=novo_valor_comissao,
                    base_calc_comissao=Decimal128(str(base_calc)) if base_calc else None,
                    cred_dev=Decimal128(str(cred_dev)) if cred_dev else None,
                    observacao=observacao,
                    data_ini=data_ini_datetime,
                    data_fim=data_fim_datetime,
                    alteracoes=[log_entry]
                )
            
            await engine.save(comissao_editada)
        
        return {"status": "success", "message": "Comissões editadas com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/comissao/edit/{data_ini}/{data_fim}")
async def get_comissao_editada(data_ini: str, data_fim: str):
    """Get edited commission values for a date range."""
    try:
        data_ini_datetime = datetime.fromisoformat(data_ini)
        data_fim_datetime = datetime.fromisoformat(data_fim)
        
        # Find all edited commissions in the date range
        collection = engine.get_collection(ComissaoEditada)
        edited = await collection.find({
            "data_comissao": {"$gte": data_ini_datetime, "$lte": data_fim_datetime}
        }).to_list(length=None)
        
        # Convert to dict format
        result = {}
        for doc in edited:
            cod_vendedor = doc.get('cod_vendedor')
            if cod_vendedor:
                result[str(cod_vendedor)] = {
                    "base_calc_comissao_editado": float(str(doc.get('base_calc_comissao_editado', 0))) if doc.get('base_calc_comissao_editado') else None,
                    "base_calc_comissao_original": float(str(doc.get('base_calc_comissao_original', 0))) if doc.get('base_calc_comissao_original') else None,
                    "vlr_comissao_editado": float(str(doc.get('vlr_comissao_editado', 0))),
                    "vlr_comissao_original": float(str(doc.get('vlr_comissao_original', 0))),
                    "observacao": doc.get('observacao', ''),
                    "alteracoes": [
                        {
                            "data_alteracao": alt.get('data_alteracao').isoformat() if alt.get('data_alteracao') else None,
                            "base_calc_anterior": float(str(alt.get('base_calc_anterior', 0))) if alt.get('base_calc_anterior') else None,
                            "base_calc_novo": float(str(alt.get('base_calc_novo', 0))) if alt.get('base_calc_novo') else None,
                            "comissao_anterior": float(str(alt.get('valor_anterior', 0))),
                            "comissao_novo": float(str(alt.get('valor_novo', 0))),
                            "observacao": alt.get('observacao', '')
                        }
                        for alt in doc.get('alteracoes', [])
                    ]
                }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/comissao/edit/log/{data_ini}/{data_fim}")
async def get_comissao_log_mes(data_ini: str, data_fim: str):
    """Get all commission alterations for a date range (month log)."""
    try:
        data_ini_datetime = datetime.fromisoformat(data_ini)
        data_fim_datetime = datetime.fromisoformat(data_fim)
        
        # Find all edited commissions in the date range
        collection = engine.get_collection(ComissaoEditada)
        edited = await collection.find({
            "data_comissao": {"$gte": data_ini_datetime, "$lte": data_fim_datetime}
        }).to_list(length=None)
        
        # Convert to dict format with all alterations
        result = {}
        for doc in edited:
            cod_vendedor = doc.get('cod_vendedor')
            if cod_vendedor:
                result[str(cod_vendedor)] = {
                    "nom_vendedor": doc.get('nom_vendedor', f"Vendedor {cod_vendedor}"),
                    "alteracoes": [
                        {
                            "data_alteracao": alt.get('data_alteracao').isoformat() if alt.get('data_alteracao') else None,
                            "base_calc_anterior": float(str(alt.get('base_calc_anterior', 0))) if alt.get('base_calc_anterior') else None,
                            "base_calc_novo": float(str(alt.get('base_calc_novo', 0))) if alt.get('base_calc_novo') else None,
                            "comissao_anterior": float(str(alt.get('valor_anterior', 0))),
                            "comissao_novo": float(str(alt.get('valor_novo', 0))),
                            "observacao": alt.get('observacao', '')
                        }
                        for alt in doc.get('alteracoes', [])
                    ]
                }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/comissao/edit-log-by-month")
async def get_comissao_edit_log_by_month(year: int, month: int):
    """
    Log of commission edits that were *made* in the given month (data_alteracao in that month).
    Returns: list of edits, sum of sales before/after per seller and for the whole store.
    """
    try:
        from calendar import monthrange
        first_day = datetime(year, month, 1)
        last_day_num = monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num, 23, 59, 59, 999999)
        
        collection = engine.get_collection(ComissaoEditada)
        all_edited = await collection.find({}).to_list(length=None)
        
        rows = []
        total_before = 0.0
        total_after = 0.0
        by_seller = {}
        
        for doc in all_edited:
            cod_vendedor = doc.get('cod_vendedor')
            nom_vendedor = doc.get('nom_vendedor') or f"Vendedor {cod_vendedor}"
            for alt in doc.get('alteracoes', []):
                data_alt = alt.get('data_alteracao')
                if not data_alt:
                    continue
                if first_day <= data_alt <= last_day:
                    base_ant = float(str(alt.get('base_calc_anterior', 0) or 0))
                    base_novo = float(str(alt.get('base_calc_novo', 0) or 0))
                    com_ant = float(str(alt.get('valor_anterior', 0) or 0))
                    com_novo = float(str(alt.get('valor_novo', 0) or 0))
                    data_alt_str = data_alt.isoformat() if hasattr(data_alt, 'isoformat') else str(data_alt)
                    rows.append({
                        "cod_vendedor": cod_vendedor,
                        "nom_vendedor": nom_vendedor,
                        "data_alteracao": data_alt_str,
                        "base_calc_anterior": base_ant,
                        "base_calc_novo": base_novo,
                        "comissao_anterior": com_ant,
                        "comissao_novo": com_novo,
                        "observacao": alt.get('observacao') or ""
                    })
                    total_before += base_ant
                    total_after += base_novo
                    key = cod_vendedor
                    if key not in by_seller:
                        by_seller[key] = {"cod_vendedor": cod_vendedor, "nom_vendedor": nom_vendedor, "sum_before": 0.0, "sum_after": 0.0}
                    by_seller[key]["sum_before"] += base_ant
                    by_seller[key]["sum_after"] += base_novo
        
        return {
            "year": year,
            "month": month,
            "rows": rows,
            "total_before": round(total_before, 2),
            "total_after": round(total_after, 2),
            "by_seller": [{"cod_vendedor": v["cod_vendedor"], "nom_vendedor": v["nom_vendedor"], "sum_before": round(v["sum_before"], 2), "sum_after": round(v["sum_after"], 2)} for v in by_seller.values()]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/comissao/edit/alteracao/{data_ini}/{data_fim}/{cod_vendedor}/{alteracao_index}")
async def excluir_alteracao(
    data_ini: str,
    data_fim: str,
    cod_vendedor: int,
    alteracao_index: int
):
    """Exclude a specific alteration from the log."""
    try:
        data_fim_datetime = datetime.fromisoformat(data_fim)
        
        # Find the ComissaoEditada record
        comissao_editada = await engine.find_one(
            ComissaoEditada,
            (ComissaoEditada.data_comissao == data_fim_datetime) & 
            (ComissaoEditada.cod_vendedor == cod_vendedor)
        )
        
        if not comissao_editada:
            raise HTTPException(status_code=404, detail="Comissão editada não encontrada")
        
        # Check if index is valid
        if alteracao_index < 0 or alteracao_index >= len(comissao_editada.alteracoes):
            raise HTTPException(status_code=400, detail="Índice de alteração inválido")
        
        # Remove the alteration at the specified index
        comissao_editada.alteracoes.pop(alteracao_index)
        comissao_editada.data_atualizacao = datetime.now()
        
        await engine.save(comissao_editada)
        
        return {"status": "success", "message": "Alteração excluída com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

