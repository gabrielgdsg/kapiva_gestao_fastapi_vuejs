from fastapi import APIRouter, HTTPException, Response, File, UploadFile, Query
from .estoque_postgres import EstoquePostgres
from ..models.estoque import ProdutoEstoquePostgres, ProdutoMovto, ProdutoEstoqueMongo, ProdutoEstoqueMongoBeanie
from ..models.levantamentos import Marcas
from db_mongo.database import engine, db
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from bson import Decimal128, ObjectId
import orjson, datetime

from odmantic import query
from typing import List
import base64

router = APIRouter()

def default(obj):
    if isinstance(obj, Decimal128):
        return str(obj)
    if isinstance(obj, ProdutoEstoqueMongo):
        return dict(obj)
    if isinstance(obj, ProdutoEstoqueMongoBeanie):
        return dict(obj)
    if isinstance(obj, ProdutoMovto):
        return dict(obj)
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d")
    raise TypeError


@router.get("/api/estoque/read_produtos_from_mongo_db/{cod_marca}")
async def read_produtos_from_mongo_db(cod_marca: int):
    if cod_marca != 0:
        produtos = await engine.find(ProdutoEstoqueMongo, ProdutoEstoqueMongo.cod_marca == cod_marca)
    else:
        produtos = await engine.find(ProdutoEstoqueMongo, ProdutoEstoqueMongo.cod_marca != 0)
    # return produtos
    return jsonable_encoder(produtos)


# TODO try to filter on backend
@router.get("/api/estoque/read_produtos_from_mongo_db_beanie/{cod_marca}/{data_movto_ini}/{data_movto_fim}")
# @router.get("/api/estoque/read_produtos_from_mongo_db_filter/{cod_marca}/{des_produto}")
async def read_produtos_from_mongo_db_beanie(cod_marca: int, data_movto_ini: str, data_movto_fim: str):
# async def read_produtos_from_mongo_db(cod_marca: int, des_produto: str):
    produtos = []
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & ProdutoEstoqueMongo.des_produto.match(des_produto))
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & ProdutoEstoqueMongo.dat_last_movto.gt('2020-01-01'))
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & ProdutoEstoqueMongo.dat_last_movto.gt(datetime.datetime("2013-10-01T00:00:00.000Z")))
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & query.gte(ProdutoEstoqueMongo.saldo_estoque,1))
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & query.gt(ProdutoEstoqueMongo.estoque_history.data_movto,'2023-03-03'))
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & query.gte(ProdutoEstoqueMongo.dat_last_movto,"2022-09-21T10:58:52.000+00:00"))
    # produtos = await engine.find(ProdutoEstoqueMongo, (ProdutoEstoqueMongo.cod_marca == cod_marca) & {'estoque_history.data_movto': {'$gt': '2023-03-03'}})
    # produtos = await db["produto_estoque_mongo"].find_one({'cod_cor': 30})

    # # TODO filter per cod_marca antes
    # async for produto in db["produto_estoque_mongo"].find({'estoque_history.data_movto': {'$gt': '2023-03-03'}}):
    #     produtos.append(produto)

    # produtos = await db["produto_estoque_mongo"].find({'estoque_history.data_movto': {'$gt': '2023-03-03'}})
    # produtos = await db["produto_estoque_mongo"].find({'estoque_history.saldo_estoque': {'$gt': 2}})
    # produtoss = await ProdutoEstoqueMongoBeanie.find(ProdutoEstoqueMongoBeanie.estoque_history.saldo_estoque > 2).to_list()
    # produtoss = await ProdutoEstoqueMongoBeanie.find({'estoque_history.data_movto': {'$gt': '2019-03-03'}}, {'estoque_history.data_movto': {'$lt': '2020-03-03'}}).to_list()
    produtoss = await ProdutoEstoqueMongoBeanie.find(ProdutoEstoqueMongoBeanie.cod_marca == cod_marca).find({'estoque_history.data_movto': {'$gt': data_movto_ini}}, {'estoque_history.data_movto': {'$lt': data_movto_fim}}).to_list()

    # return produtos
    # return jsonable_encoder(produtos)
    orjson_dump = orjson.dumps(produtoss, default=default, option=orjson.OPT_PASSTHROUGH_DATETIME)
    return Response(orjson_dump, media_type='application/json')




@router.get("/api/estoque/read_produtos_from_mongo_db_test/{cod_marca}")
async def read_produtos_from_mongo_db(cod_marca: int):
    if cod_marca != 0:
        produtos = await engine.find(ProdutoEstoqueMongo, ProdutoEstoqueMongo.cod_marca == cod_marca)
    else:
        produtos = await engine.find(ProdutoEstoqueMongo, ProdutoEstoqueMongo.cod_marca != 0)
    orjson_dump = orjson.dumps(produtos, default=default, option=orjson.OPT_PASSTHROUGH_DATETIME)
    return Response(orjson_dump, media_type='application/json')
    # return jsonable_encoder(produtos)


@router.get("/api/estoque/read_produtos_from_postgres_db/{cod_marca}/{dat_movto_ini}")
async def read_produtos_from_postgres_db(cod_marca: str, dat_movto_ini: str):
    # TODO check if dat_movto_ini is not date
    if dat_movto_ini == ' ':
        dat_movto_ini = '1994-04-01'

    marcas = await engine.find(Marcas, Marcas.cod_marca != 'NoNe')
    if cod_marca not in marcas:
        print('cod_marca not in marcas')
    else:
        marcas.append(cod_marca)

    for i in range(len(marcas[0:10])):
        produtos_da_marca = EstoquePostgres.load_estoque_produtos_from_db(marcas[i].cod_marca, dat_movto_ini)

        produtos_estoque_list = []
        dict_cod_mov_estoque = {2: 'Emissao nota fiscal', 3: 'Requisicao', 4: 'Devolucao', 7: 'Entr. proc. notas',
                                9: 'Frente de caixa', 12: 'Estorno proc. notas', 15: 'Condicional'}

        for i in range(len(produtos_da_marca)):
            if produtos_da_marca[i][21] is None:
                dat_ultcompra_default = datetime.strptime("1900-01-01", "%Y-%m-%d")
            else:
                dat_ultcompra_default = produtos_da_marca[i][21]

            produto_estoque = ProdutoEstoquePostgres(
                cod_grupo=produtos_da_marca[i][0],
                des_grupo=produtos_da_marca[i][1],
                cod_subgrupo=produtos_da_marca[i][2],
                des_subgrupo=produtos_da_marca[i][3],
                cod_produto=produtos_da_marca[i][4],
                des_produto=produtos_da_marca[i][5],
                cod_barra=produtos_da_marca[i][6],
                cod_referencia=produtos_da_marca[i][7],
                qtd=produtos_da_marca[i][8],
                saldo_estoque_prod=produtos_da_marca[i][9],
                vlr_custo_bruto=produtos_da_marca[i][10],
                vlr_custo_aquis=produtos_da_marca[i][11],
                vlr_venda1=produtos_da_marca[i][12],
                total=produtos_da_marca[i][13],
                cod_grade=produtos_da_marca[i][14],
                des_grade=produtos_da_marca[i][15],
                cod_tamanho=produtos_da_marca[i][16],
                des_tamanho=produtos_da_marca[i][17],
                cod_cor=produtos_da_marca[i][18],
                des_cor=produtos_da_marca[i][19],
                dat_cadastro=produtos_da_marca[i][20].replace(microsecond=0),
                dat_ultcompra=datetime.combine(dat_ultcompra_default, datetime.min.time()),
                cod_fornecedor=produtos_da_marca[i][22],
                raz_fornecedor=produtos_da_marca[i][23],
                fan_fornecedor=produtos_da_marca[i][24],
                cod_marca=produtos_da_marca[i][25],
                nom_marca=produtos_da_marca[i][26],
                tipo_movto=produtos_da_marca[i][27],
                qtd_movto=produtos_da_marca[i][28],
                dat_movto=produtos_da_marca[i][29].replace(microsecond=0),
                cod_movto=produtos_da_marca[i][30],
                cod_origem_movto=produtos_da_marca[i][31],
                des_movto=dict_cod_mov_estoque.get(produtos_da_marca[i][31], 'outro'),
                id_movto=produtos_da_marca[i][32],
                # img=base64.b64encode('iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII='),
                # img='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=',
                list_produto_movtos=[],
                dat_last_movto=datetime.strptime("1900-01-01 01:00:00", "%Y-%m-%d %H:%M:%S").replace(microsecond=0)
                # dat_atualizacao=datetime.today()
                )
            produtos_estoque_list.append(produto_estoque)



        for produto in produtos_estoque_list:

            db_produto = await engine.find_one(ProdutoEstoqueMongo,
                                               ProdutoEstoqueMongo.cod_referencia == produto.cod_referencia,
                                               ProdutoEstoqueMongo.cod_marca == produto.cod_marca,
                                               ProdutoEstoqueMongo.des_cor == produto.des_cor)
            # saldo_estoque = 0  # TODO
            # saldo_estoque_E = 0 #TODO

            if db_produto is None:
                dat_prior_first_movto = datetime.strptime(str(produto.dat_movto - timedelta(1)),"%Y-%m-%d %H:%M:%S").replace(microsecond=0)
                db_produto = ProdutoEstoqueMongo(**produto.__dict__,**{"saldo_estoque": 0,"saldo_estoque_e": 0,'saidas': 0, "estoque_ratio": 0, "estoque_vel": 0, "estoque_history": [{ 'data_movto': str(dat_prior_first_movto), 'saldo_estoque': 0,
                                                                      'saldo_estoque_e': 0,'saidas': 0,
                                                                      'grade_estoque': {}}], "flag": False})


            if next((db_movto for db_movto in db_produto.list_produto_movtos if db_movto.id_movto == produto.id_movto), None) is None:
                produto_movto = ProdutoMovto(dat_movto=produto.dat_movto, tipo_movto=produto.tipo_movto, cod_movto=produto.cod_movto, cod_origem_movto=produto.cod_origem_movto,
                                               des_movto=produto.des_movto, id_movto=produto.id_movto)
                setattr(produto_movto, produto.des_tamanho, produto.qtd_movto)
                db_produto.dat_last_movto = produto.dat_movto
                db_produto.list_produto_movtos.append(produto_movto)
                saldo_estoque_ant = db_produto.saldo_estoque

                # #calculo saldo_estoque________________________________________
                # # tentar colocar esse calculo do saldo_estoque dentro de outro loop TODO
                # # tentar calcular o saldo de entrada também TODO
                # if produto.tipo_movto == 'E':
                #     db_produto.saldo_estoque = db_produto.saldo_estoque + produto.qtd_movto
                #
                # elif produto.tipo_movto == 'S':
                #     db_produto.saldo_estoque = db_produto.saldo_estoque - produto.qtd_movto
                #
                # db_produto.estoque_history[str(produto.dat_movto)] = {'saldo_estoque': db_produto.saldo_estoque,
                #                                                           'id_movto': produto.id_movto,
                #                                                           'des_tamanho': produto.des_tamanho}
                # # calculo saldo_estoque________________________________________
                #TODO
                # ________________copy&paste_________________________________________________________________________________
                # calculdo das entradas '_E' da grade_estoque
                if produto.tipo_movto == 'E' and (produto.cod_origem_movto == 7 or produto.cod_origem_movto == 3):
                    if produto.des_tamanho + '_E' in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = db_produto.grade_estoque[produto.des_tamanho + '_E'] + produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = produto.qtd_movto
                    db_produto.saldo_estoque_e = db_produto.saldo_estoque_e + produto.qtd_movto
                elif produto.tipo_movto == 'S' and (produto.cod_origem_movto == 12 or produto.cod_origem_movto == 3):
                    if produto.des_tamanho == '39-42':
                        print('pause')
                    if produto.des_tamanho + '_E' in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = db_produto.grade_estoque[produto.des_tamanho + '_E'] - produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = 0 - produto.qtd_movto
                    db_produto.saldo_estoque_e = db_produto.saldo_estoque_e - produto.qtd_movto

                # calculo da quantidade atual da grade_estoque
                if produto.tipo_movto == 'E':
                    db_produto.saldo_estoque = db_produto.saldo_estoque + produto.qtd_movto
                    if produto.des_tamanho in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho] = db_produto.grade_estoque[produto.des_tamanho] + produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho] = produto.qtd_movto
                elif produto.tipo_movto == 'S':
                    db_produto.saldo_estoque = db_produto.saldo_estoque - produto.qtd_movto
                    if produto.des_tamanho in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho] = db_produto.grade_estoque[produto.des_tamanho] - produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho] = 0 - produto.qtd_movto

                # calculo das saídas da grade_estoque
                if produto.tipo_movto == 'E' and produto.cod_origem_movto == 4:
                    db_produto.saidas = db_produto.saidas + produto.qtd_movto
                elif produto.tipo_movto == 'S' and (produto.cod_origem_movto == 2 or produto.cod_origem_movto == 9):
                    db_produto.saidas = db_produto.saidas - produto.qtd_movto

                # db_produto.estoque_history.append({'data_movto': str(produto.dat_movto),
                db_produto.estoque_history.append({'data_movto': str(produto.dat_movto),
                                                                      'saldo_estoque': db_produto.saldo_estoque,
                                                                      'saldo_estoque_ant': saldo_estoque_ant,
                                                                      'saidas': db_produto.saidas,
                                                                      'saldo_estoque_e': db_produto.saldo_estoque_e,
                                                                      'grade_estoque': db_produto.grade_estoque,
                                                                      'qtd_movto': produto.qtd_movto,
                                                                      'id_movto': produto.id_movto,
                                                                      'cod_movto': produto.cod_movto,
                                                                      'tipo_movto': produto.tipo_movto,
                                                                      'des_movto': produto.des_movto,
                                                                      'cod_origem_movto': produto.cod_origem_movto})
                # db_produto.saldo_estoque = db_produto.saldo_estoque + db_produto.grade_estoque[produto.des_tamanho]
                # db_produto.estoque_history[str(produto.dat_movto)] = {'saldo_estoque': db_produto.saldo_estoque,
                #                                                       'id_movto': produto.id_movto,
                #                                                       'des_tamanho': produto.des_tamanho}


                #_________________________________________________________________________________________________

            # else:
                # print('No product should enter this else after deleting produto_estoque_mongo')
                # print("db_produto"+ str(db_produto)+ '=' "produto"+ str(produto.id_movto))


            await engine.save(db_produto)


@router.get("/api/estoque/read_produtos_from_postgres_db_beanie/{cod_marca}/{dat_movto_ini}", response_model_by_alias=False)


async def read_produtos_from_postgres_db_beanie(cod_marca: str, dat_movto_ini: str):
    db_produto = []
    # TODO check if dat_movto_ini is not date
    if dat_movto_ini == ' ':
        dat_movto_ini = '1994-04-01'

    marcas = await engine.find(Marcas, Marcas.cod_marca != 'NoNe')
    if cod_marca not in marcas:
        print('cod_marca not in marcas')
    else:
        marcas.append(cod_marca)

    for i in range(len(marcas[0:1000])):
        produtos_da_marca = EstoquePostgres.load_estoque_produtos_from_db(marcas[i].cod_marca, dat_movto_ini)

        produtos_estoque_list = []
        dict_cod_mov_estoque = {2: 'Emissao nota fiscal', 3: 'Requisicao', 4: 'Devolucao',
                                7: 'Entr. proc. notas',
                                9: 'Frente de caixa', 12: 'Estorno proc. notas', 15: 'Condicional'}

        for i in range(len(produtos_da_marca)):
            if produtos_da_marca[i][21] is None:
                dat_ultcompra_default = datetime.datetime.strptime("1900-01-01", "%Y-%m-%d")
            else:
                dat_ultcompra_default = produtos_da_marca[i][21]

            produto_estoque = ProdutoEstoquePostgres(
                cod_grupo=produtos_da_marca[i][0],
                des_grupo=produtos_da_marca[i][1],
                cod_subgrupo=produtos_da_marca[i][2],
                des_subgrupo=produtos_da_marca[i][3],
                cod_produto=produtos_da_marca[i][4],
                des_produto=produtos_da_marca[i][5],
                cod_barra=produtos_da_marca[i][6],
                cod_referencia=produtos_da_marca[i][7],
                qtd=produtos_da_marca[i][8],
                saldo_estoque_prod=produtos_da_marca[i][9],
                vlr_custo_bruto=produtos_da_marca[i][10],
                vlr_custo_aquis=produtos_da_marca[i][11],
                vlr_venda1=produtos_da_marca[i][12],
                total=produtos_da_marca[i][13],
                cod_grade=produtos_da_marca[i][14],
                des_grade=produtos_da_marca[i][15],
                cod_tamanho=produtos_da_marca[i][16],
                des_tamanho=produtos_da_marca[i][17],
                cod_cor=produtos_da_marca[i][18],
                des_cor=produtos_da_marca[i][19],
                dat_cadastro=produtos_da_marca[i][20].replace(microsecond=0),
                dat_ultcompra=datetime.datetime.combine(dat_ultcompra_default, datetime.datetime.min.time()),
                cod_fornecedor=produtos_da_marca[i][22],
                raz_fornecedor=produtos_da_marca[i][23],
                fan_fornecedor=produtos_da_marca[i][24],
                cod_marca=produtos_da_marca[i][25],
                nom_marca=produtos_da_marca[i][26],
                tipo_movto=produtos_da_marca[i][27],
                qtd_movto=produtos_da_marca[i][28],
                dat_movto=produtos_da_marca[i][29].replace(microsecond=0),
                cod_movto=produtos_da_marca[i][30],
                cod_origem_movto=produtos_da_marca[i][31],
                des_movto=dict_cod_mov_estoque.get(produtos_da_marca[i][31], 'outro'),
                id_movto=produtos_da_marca[i][32],
                # img=base64.b64encode('iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII='),
                # img='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=',
                list_produto_movtos=[],
                dat_last_movto=datetime.datetime.strptime("1900-01-01 01:00:00", "%Y-%m-%d %H:%M:%S").replace(
                    microsecond=0)
                # dat_atualizacao=datetime.today()
            )
            produtos_estoque_list.append(produto_estoque)

        for produto in produtos_estoque_list:

            db_produto = await ProdutoEstoqueMongoBeanie.find(
                                               ProdutoEstoqueMongoBeanie.cod_referencia == produto.cod_referencia,
                                               ProdutoEstoqueMongoBeanie.cod_marca == produto.cod_marca,
                                               ProdutoEstoqueMongoBeanie.des_cor == produto.des_cor).first_or_none()
            # db_produto = await ProdutoEstoqueMongoBeanie.find().first_or_none()
            # saldo_estoque = 0  # TODO
            # saldo_estoque_E = 0 #TODO
            # estoque_vel and estoque_ratio as int ---> turn into Decimal TODO

            if db_produto is None:
                dat_prior_first_movto = datetime.datetime.strptime(str(produto.dat_movto - timedelta(1)),
                                                          "%Y-%m-%d %H:%M:%S").replace(microsecond=0)
                db_produto = ProdutoEstoqueMongoBeanie(**produto.__dict__,
                                                 **{"saldo_estoque": 0, "saldo_estoque_e": 0, 'saidas': 0,
                                                    "estoque_ratio": 0, "estoque_vel": 0.0, "estoque_history": [
                                                         {'data_movto': str(dat_prior_first_movto),
                                                          'saldo_estoque': 0,
                                                          'saldo_estoque_e': 0, 'saidas': 0,
                                                          'grade_estoque': {}}], "flag": False})

            if next((db_movto for db_movto in db_produto.list_produto_movtos if
                     db_movto.id_movto == produto.id_movto), None) is None:
                produto_movto = ProdutoMovto(dat_movto=produto.dat_movto, tipo_movto=produto.tipo_movto,
                                             cod_movto=produto.cod_movto,
                                             cod_origem_movto=produto.cod_origem_movto,
                                             des_movto=produto.des_movto, id_movto=produto.id_movto)
                setattr(produto_movto, produto.des_tamanho, produto.qtd_movto)
                db_produto.dat_last_movto = produto.dat_movto
                db_produto.list_produto_movtos.append(produto_movto)
                saldo_estoque_ant = db_produto.saldo_estoque

                # #calculo saldo_estoque________________________________________
                # # tentar colocar esse calculo do saldo_estoque dentro de outro loop TODO
                # # tentar calcular o saldo de entrada também TODO
                # if produto.tipo_movto == 'E':
                #     db_produto.saldo_estoque = db_produto.saldo_estoque + produto.qtd_movto
                #
                # elif produto.tipo_movto == 'S':
                #     db_produto.saldo_estoque = db_produto.saldo_estoque - produto.qtd_movto
                #
                # db_produto.estoque_history[str(produto.dat_movto)] = {'saldo_estoque': db_produto.saldo_estoque,
                #                                                           'id_movto': produto.id_movto,
                #                                                           'des_tamanho': produto.des_tamanho}
                # # calculo saldo_estoque________________________________________
                # TODO
                # ________________copy&paste_________________________________________________________________________________
                # calculdo das entradas '_E' da grade_estoque
                if produto.tipo_movto == 'E' and (
                        produto.cod_origem_movto == 7 or produto.cod_origem_movto == 3):
                    if produto.des_tamanho + '_E' in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = db_produto.grade_estoque[
                                                                                   produto.des_tamanho + '_E'] + produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = produto.qtd_movto
                    db_produto.saldo_estoque_e = db_produto.saldo_estoque_e + produto.qtd_movto
                elif produto.tipo_movto == 'S' and (
                        produto.cod_origem_movto == 12 or produto.cod_origem_movto == 3):
                    if produto.des_tamanho == '39-42':
                        print('pause')
                    if produto.des_tamanho + '_E' in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = db_produto.grade_estoque[
                                                                                   produto.des_tamanho + '_E'] - produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho + '_E'] = 0 - produto.qtd_movto
                    db_produto.saldo_estoque_e = db_produto.saldo_estoque_e - produto.qtd_movto

                # calculo da quantidade atual da grade_estoque
                if produto.tipo_movto == 'E':
                    db_produto.saldo_estoque = db_produto.saldo_estoque + produto.qtd_movto
                    if produto.des_tamanho in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho] = db_produto.grade_estoque[
                                                                            produto.des_tamanho] + produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho] = produto.qtd_movto
                elif produto.tipo_movto == 'S':
                    db_produto.saldo_estoque = db_produto.saldo_estoque - produto.qtd_movto
                    if produto.des_tamanho in db_produto.grade_estoque:
                        db_produto.grade_estoque[produto.des_tamanho] = db_produto.grade_estoque[
                                                                            produto.des_tamanho] - produto.qtd_movto
                    else:
                        db_produto.grade_estoque[produto.des_tamanho] = 0 - produto.qtd_movto

                # calculo das saídas da grade_estoque
                if produto.tipo_movto == 'E' and produto.cod_origem_movto == 4:
                    db_produto.saidas = db_produto.saidas + produto.qtd_movto
                elif produto.tipo_movto == 'S' and (
                        produto.cod_origem_movto == 2 or produto.cod_origem_movto == 9):
                    db_produto.saidas = db_produto.saidas - produto.qtd_movto

                # db_produto.estoque_history.append({'data_movto': str(produto.dat_movto),
                db_produto.estoque_history.append({'data_movto': produto.dat_movto,
                                                   'saldo_estoque': db_produto.saldo_estoque,
                                                   'saldo_estoque_ant': saldo_estoque_ant,
                                                   'saidas': db_produto.saidas,
                                                   'saldo_estoque_e': db_produto.saldo_estoque_e,
                                                   'grade_estoque': db_produto.grade_estoque,
                                                   'qtd_movto': produto.qtd_movto,
                                                   'id_movto': produto.id_movto,
                                                   'cod_movto': produto.cod_movto,
                                                   'tipo_movto': produto.tipo_movto,
                                                   'des_movto': produto.des_movto,
                                                   'cod_origem_movto': produto.cod_origem_movto})
                # db_produto.saldo_estoque = db_produto.saldo_estoque + db_produto.grade_estoque[produto.des_tamanho]
                # db_produto.estoque_history[str(produto.dat_movto)] = {'saldo_estoque': db_produto.saldo_estoque,
                #                                                       'id_movto': produto.id_movto,
                #                                                       'des_tamanho': produto.des_tamanho}

                # _________________________________________________________________________________________________

            # else:
            # print('No product should enter this else after deleting produto_estoque_mongo')
            # print("db_produto"+ str(db_produto)+ '=' "produto"+ str(produto.id_movto))

            await db_produto.save()
            # await db_produto.dict().save()

        # produto_estoque_list = []
        # data_current_datetime = datetime.fromisoformat()
        # for i in range(len(produtos_da_marca)):
        #     produto_estoque = ProdutoEstoque(
        #     cod_grupo: produtos_da_marca[i][0],
        #     des_grupo: produtos_da_marca[i][1],
        #     cod_subgrupo: produtos_da_marca[i][2],
        #     des_subgrupo: produtos_da_marca[i][3],
        #     cod_produto: produtos_da_marca[i][4],
        #     des_produto: produtos_da_marca[i][5],
        #     vlr_custo_bruto: produtos_da_marca[i][0],
        #     vlr_custo_aquis: produtos_da_marca[i][0],
        #     vlr_venda1: produtos_da_marca[i][0],
        #     cod_grade: produtos_da_marca[i][0],
        #     des_grade: produtos_da_marca[i][0],
        #     list_produto_grade: ProdutoGrade,
        #     list_produto_movtos: List[ProdutoMovto],
        #     cod_cor: produtos_da_marca[i][0],
        #     dat_cadastro: produtos_da_marca[i][0],
        #     dat_ultcompra: produtos_da_marca[i][0],
        #     cod_fornecedor: produtos_da_marca[i][0],
        #     raz_fornecedor: produtos_da_marca[i][0],
        #     fan_fornecedor: produtos_da_marca[i][0],
        #     cod_marca: produtos_da_marca[i][0],
        #     cod_referencia: produtos_da_marca[i][0],
        #     nom_marca: produtos_da_marca[i][0],
        #     des_cor: produtos_da_marca[i][0],
        #     img: binData,
        #     ratio: 0,
        #     flag: false
        #
        #         cod_vendedor=produtos_da_marca[i][0],
        #                                          nom_vendedor=comissao_loaded[i][1],
        #                                          base_calc_comissao=comissao_loaded[i][2],
        #                                          vlr_comissao=comissao_loaded[i][4],
        #                                          cred_dev=comissao_loaded[i][3],
        #                                          data_ini=datetime.fromisoformat(data_ini),
        #                                          data_fim=datetime.fromisoformat(data_fim))
        #     produto_estoque_list.append(produto_estoque)
        #
        #
        #     novo_estoque_produtos = EstoqueProdutos(datetime_atualizacao=data_current_datetime,
        #                                     list_produtos=produto_estoque_list)

        # await save_produtos(novo_estoque_produtos)
    return jsonable_encoder(produtos_da_marca)


# @router.put("/api/estoque/save_produtos")
# async def save_produtos(list_produtos: List[ProdutoEstoque]):
#     produtos_to_save = []
#     for produto in list_produtos:
#         db_produto = await engine.find_one(ProdutoEstoque,
#                                            ProdutoEstoque.cod_referencia == produto.cod_referencia,
#                                            ProdutoEstoque.nom_marca == produto.nom_marca,
#                                            ProdutoEstoque.des_cor == produto.des_cor)
#         print(f'db_produto{db_produto}')
#         print(f'produto: {produto}')
#         if db_produto is not None:
#             db_produto.img = produto.img
#             produtos_to_save.append(db_produto)
#         else:
#             produtos_to_save.append(produto)
#
#     EstoqueProdutos.datetime_atualizacao = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
#     await engine.save(produtos_to_save)
#     # await engine.save_all(produtos_to_save)
#     return "db_updated"


# @router.put("/api/estoque/read_produtos/")
# async def read_produtos(estoque_produtos: EstoqueProdutos):
# # async def get_produtos(produtos: Optional[List[Produto]] = Query(None)):
#     estoque_produtos_list = []
#     for produto in estoque_produtos.list_produtos:
#         db_estoque_produtos = await engine.find_one(ProdutoEstoque,
#                                            ProdutoEstoque.cod_referencia == produto.cod_referencia,
#                                            ProdutoEstoque.nom_marca == produto.nom_marca,
#                                            ProdutoEstoque.des_cor == produto.des_cor,
#                                            ProdutoEstoque.des_produto == produto.des_produto)
#         if db_estoque_produtos is not None:
#             estoque_produtos_list.append(db_estoque_produtos)
#         else:
#             estoque_produtos_list.append(estoque_produtos)
#     return jsonable_encoder(estoque_produtos_list)


@router.get("/api/estoque/update/{dat_movto_ini}")
async def update_estoque(dat_movto_ini: str):
    estoque_loaded = EstoquePostgres.load_estoque_produtos_from_db(dat_movto_ini)
    return jsonable_encoder(estoque_loaded)
