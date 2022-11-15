from fastapi import APIRouter, HTTPException, Response, File, UploadFile, Query
from .estoque_postgres import EstoquePostgres
from ..models.estoque import EstoqueProdutos, ProdutoEstoque
from db_mongo.database import engine
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.get("/api/estoque/read_produtos_por_marca/{cod_marca}")
async def read_produtos_por_marca(cod_marca: str):
    produtos_da_marca = EstoquePostgres.load_produtos_from_db(cod_marca)
    return jsonable_encoder(produtos_da_marca)


@router.put("/api/estoque/save_produtos")
async def save_produtos(list_produtos: List[ProdutoEstoque]):
    produtos_to_save = []
    for produto in list_produtos:
        db_produto = await engine.find_one(ProdutoEstoque,
                                           ProdutoEstoque.cod_referencia == produto.cod_referencia,
                                           ProdutoEstoque.nom_marca == produto.nom_marca,
                                           ProdutoEstoque.des_cor == produto.des_cor,
                                           ProdutoEstoque.des_produto == produto.des_produto)
        print(f'db_produto{db_produto}')
        print(f'produto: {produto}')
        if db_produto is not None:
            db_produto.img = produto.img
            produtos_to_save.append(db_produto)
        else:
            produtos_to_save.append(produto)

    EstoqueProdutos.datetime_atualizacao =  datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    await engine.save(produtos_to_save)
    # await engine.save_all(produtos_to_save)
    return "db_updated"

@router.put("/api/estoque/read_produtos/")
async def read_produtos(estoque_produtos: EstoqueProdutos):
# async def get_produtos(produtos: Optional[List[Produto]] = Query(None)):
    estoque_produtos_list = []
    for produto in estoque_produtos.list_produtos:
        db_estoque_produtos = await engine.find_one(ProdutoEstoque,
                                           ProdutoEstoque.cod_referencia == produto.cod_referencia,
                                           ProdutoEstoque.nom_marca == produto.nom_marca,
                                           ProdutoEstoque.des_cor == produto.des_cor,
                                           ProdutoEstoque.des_produto == produto.des_produto)
        if db_estoque_produtos is not None:
            estoque_produtos_list.append(db_estoque_produtos)
        else:
            estoque_produtos_list.append(estoque_produtos)
    return jsonable_encoder(estoque_produtos_list)

