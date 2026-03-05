from fastapi import APIRouter, HTTPException
from .comissao_postgres import ComissaoPostgres
from ..models.comissao import ComissaoVendedor, ComissaoDia
from db_mongo.database import engine
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder

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
                comissao_vendedor = ComissaoVendedor(cod_vendedor=comissao_loaded[i][0],
                                                     nom_vendedor=comissao_loaded[i][1],
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

