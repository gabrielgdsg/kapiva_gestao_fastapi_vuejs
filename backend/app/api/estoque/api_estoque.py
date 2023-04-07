from fastapi import APIRouter, HTTPException, Response, File, UploadFile, Query
from .estoque_postgres import EstoquePostgres
from ..models.estoque import ProdutoEstoquePostgres, ProdutoMovto, ProdutoEstoqueMongo
from db_mongo.database import engine
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import List
import base64

router = APIRouter()


@router.get("/api/estoque/read_produtos_from_mongo_db/{cod_marca}")
async def read_produtos_from_mongo_db(cod_marca: int):
    produtos = await engine.find(ProdutoEstoqueMongo, ProdutoEstoqueMongo.cod_marca == cod_marca)
    return jsonable_encoder(produtos)


@router.get("/api/estoque/read_produtos_from_postgres_db/{cod_marca}/{dat_movto_ini}")
async def read_produtos_from_postgres_db(cod_marca: str, dat_movto_ini: str):
    produtos_da_marca = EstoquePostgres.load_estoque_produtos_from_db(cod_marca, dat_movto_ini)

    produtos_estoque_list = []
    dict_cod_mov_estoque = {2: 'Emissao nota fiscal', 3: 'requisicao', 4: 'devolucao', 7: 'Entr. proc. notas',
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
            saldo_estoque=produtos_da_marca[i][9],
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
            des_movto=dict_cod_mov_estoque.get(produtos_da_marca[i][31]),
            id_movto=produtos_da_marca[i][32],
            # img=base64.b64encode('iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII='),
            # img='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=',
            ratio=0,
            flag=False,
            list_produto_movtos=[],
            dat_last_movto=datetime.strptime("1900-01-01 01:15:32", "%Y-%m-%d %H:%M:%S").replace(microsecond=0)
            # dat_atualizacao=datetime.today()
            )
        produtos_estoque_list.append(produto_estoque)

    for produto in produtos_estoque_list:
        db_produto = await engine.find_one(ProdutoEstoqueMongo,
                                           ProdutoEstoqueMongo.cod_referencia == produto.cod_referencia,
                                           ProdutoEstoqueMongo.cod_marca == produto.cod_marca,
                                           ProdutoEstoqueMongo.des_cor == produto.des_cor)

        if db_produto is None:
            db_produto = ProdutoEstoqueMongo(**produto.__dict__)



        if next((db_movto for db_movto in db_produto.list_produto_movtos if db_movto.id_movto == produto.id_movto), None) is None:

            produto_movto = ProdutoMovto(dat_movto=produto.dat_movto, tipo_movto=produto.tipo_movto, cod_movto=produto.cod_movto, cod_origem_movto=produto.cod_origem_movto,
                                           des_movto=produto.des_movto, id_movto=produto.id_movto)
            setattr(produto_movto, produto.des_tamanho, produto.qtd_movto)
            db_produto.dat_last_movto = produto.dat_movto
            db_produto.list_produto_movtos.append(produto_movto)

            # ________________copy&paste_________________________________________________________________________________
            # calculdo das entradas '_E' da grade_estoque
            if produto.tipo_movto == 'E' and produto.cod_origem_movto == 7:

                if produto.des_tamanho + '_E' in db_produto.grade_estoque:
                    db_produto.grade_estoque[produto.des_tamanho + '_E'] = db_produto.grade_estoque[produto.des_tamanho + '_E'] + produto.qtd_movto
                else:
                    db_produto.grade_estoque[produto.des_tamanho + '_E'] = produto.qtd_movto

            elif produto.tipo_movto == 'S' and produto.cod_origem_movto == 12:
                db_produto.grade_estoque[produto.des_tamanho + '_E'] = db_produto.grade_estoque[produto.des_tamanho + '_E'] - produto.qtd_movto

            # calculo da quantidade atual da grade_estoque
            if produto.tipo_movto == 'E':
                if produto.des_tamanho in db_produto.grade_estoque:
                    db_produto.grade_estoque[produto.des_tamanho] = db_produto.grade_estoque[produto.des_tamanho] + produto.qtd_movto
                else:
                    db_produto.grade_estoque[produto.des_tamanho] = produto.qtd_movto
            elif produto.tipo_movto == 'S':
                if produto.des_tamanho in db_produto.grade_estoque:
                    db_produto.grade_estoque[produto.des_tamanho] = db_produto.grade_estoque[produto.des_tamanho] - produto.qtd_movto
                else:
                    db_produto.grade_estoque[produto.des_tamanho] = 0 - produto.qtd_movto
            #_________________________________________________________________________________________________

        # else:
            # print('No product should enter this else after deleting produto_estoque_mongo')
            # print("db_produto"+ str(db_produto)+ '=' "produto"+ str(produto.id_movto))

        # print(db_produto.grade_estoque)

        # mongo_db_produto = ProdutoEstoqueMongo(**db_produto.__dict__)

        # if db_produto.cod_referencia == 'OLY 001':
        #     print('produto')
        #     print(produto)
        #     print('db_produto')
        #     print(db_produto)

        await engine.save(db_produto)
        # await engine.save(mongo_db_produto)


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
