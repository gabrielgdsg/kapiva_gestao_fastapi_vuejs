from fastapi import APIRouter, HTTPException, Response, File, UploadFile, Query
from fastapi.responses import FileResponse
from .levantamentos_postgres import LevantamentoPostgres
from ..models.levantamentos import LevantamentoEstoque, MarcaFornecedor, Marcas, Fornecedor, Produto
from db_mongo.database import engine
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
import base64
import requests
from typing import List, Optional

router = APIRouter()


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
async def read_levantamentos(data_cadastro_ini: str, data_cadastro_fim: str, cod_marca: str):
    data_cadastro_ini_datetime = datetime.fromisoformat(data_cadastro_ini)
    data_cadastro_fim_datetime = datetime.fromisoformat(data_cadastro_fim)

    levantamento_loaded = LevantamentoPostgres.load_estoque_from_db(data_cadastro_ini, data_cadastro_fim, cod_marca)
    # levantamento_estoque_list = [LevantamentoEstoque(
    #         cod_grupo=levantamento_loaded[i][0], des_grupo=levantamento_loaded[i][1],
    #         cod_subgrupo=levantamento_loaded[i][2], des_subgrupo=levantamento_loaded[i][3],
    #         cod_produto=levantamento_loaded[i][4], des_produto=levantamento_loaded[i][5],
    #         cod_barra=levantamento_loaded[i][6], cod_referencia=levantamento_loaded[i][7],
    #         qtd=levantamento_loaded[i][8], saldo_estoque=levantamento_loaded[i][9],
    #         vlr_custo_bruto=levantamento_loaded[i][10], vlr_custo_aquis=levantamento_loaded[i][11],
    #         vlr_venda1=levantamento_loaded[i][12], total=levantamento_loaded[i][13],
    #         cod_grade=levantamento_loaded[i][14], des_grade=levantamento_loaded[i][15],
    #         cod_tamanho=levantamento_loaded[i][16], des_tamanho=levantamento_loaded[i][17],
    #         cod_cor=levantamento_loaded[i][18], des_cor=levantamento_loaded[i][19],
    #         dat_cadastro=levantamento_loaded[i][20], dat_alteracao=levantamento_loaded[i][21],
    #         dat_emissao=levantamento_loaded[i][22], dat_lancamento=levantamento_loaded[i][23],
    #         dat_saida=levantamento_loaded[i][24], cod_fornecedor=levantamento_loaded[i][25],
    #         raz_fornecedor=levantamento_loaded[i][26], fan_fornecedor=levantamento_loaded[i][27],
    #         cod_marca=levantamento_loaded[i][28], nom_marca=levantamento_loaded[i][29],
    #         tipo_movto=levantamento_loaded[i][30], qtd_movto=levantamento_loaded[i][31], data_movto=levantamento_loaded[i][32],
    #         cod_movto=levantamento_loaded[i][33], cod_origem_movto=levantamento_loaded[i][34]) for i, _ in enumerate(levantamento_loaded)]

    # return jsonable_encoder(levantamento_estoque_list)
    return jsonable_encoder(levantamento_loaded)


@router.get("/api/reloadfrompostgresdb/marcafornecedor/")
async def reloadfrompostgresdb_marcafornecedor():
    marcas_fornecedores = await engine.find(MarcaFornecedor)
    for marca_fornecedor in marcas_fornecedores:
        await engine.delete(marca_fornecedor)

    dados_marcas_fornecedores = LevantamentoPostgres.load_marcas_fornecedores_from_db()
    marcas_fornecedores_list = []
    marcas_list = []
    fornecedor_list = []

    for i in range(len(dados_marcas_fornecedores)):
        marca_fornecedor = MarcaFornecedor(
            cod_marca=dados_marcas_fornecedores[i][3], nom_marca=dados_marcas_fornecedores[i][4],
            cod_fornecedor=dados_marcas_fornecedores[i][0], raz_fornecedor=dados_marcas_fornecedores[i][1],
            fan_fornecedor=dados_marcas_fornecedores[i][2]
        )
        marcas_fornecedores_list.append(marca_fornecedor)

        fornecedor = Fornecedor(cod_fornecedor=dados_marcas_fornecedores[i][0],
                                raz_fornecedor=dados_marcas_fornecedores[i][1],
                                fan_fornecedor=dados_marcas_fornecedores[i][2])

        if dados_marcas_fornecedores[i][4] == (
        dados_marcas_fornecedores[i + 1][4] if i < len(dados_marcas_fornecedores) - 1
        else None):
            fornecedor_list.append(fornecedor)
        else:
            fornecedor_list.append(fornecedor)
            marca = Marcas(cod_marca=dados_marcas_fornecedores[i][3], nom_marca=dados_marcas_fornecedores[i][4],
                           fornecedores=fornecedor_list)
            fornecedor_list = []
            marcas_list.append(marca)
    await engine.save_all(marcas_fornecedores_list)
    await engine.save_all(marcas_list)
    return jsonable_encoder(marcas_list)
    # return jsonable_encoder(marcas_fornecedores_list)


# @router.get("/api/read/marcafornecedor/")
# async def read_marcafornecedor():
#     marcas_fornecedores_obj = await engine.find(MarcaFornecedor)
#     return jsonable_encoder(marcas_fornecedores_obj)


@router.get("/api/read/marcas/")
async def read_marcas():
    marcas_obj = await engine.find(Marcas)
    return jsonable_encoder(marcas_obj)


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


@router.put("/api/produtos/save")
async def save_produtos(produtos: List[Produto]):
    produtos_to_save = []
    for produto in produtos:
        db_produto = await engine.find_one(Produto,
                                           Produto.cod_referencia == produto.cod_referencia,
                                           Produto.nom_marca == produto.nom_marca,
                                           Produto.des_cor == produto.des_cor)
        print(f'db_produto{db_produto}')
        print(f'produto: {produto}')
        if db_produto is not None:
            # Creating a new instance of db_produto with 'id' from the existant one
            # db_produto_to_update = Produto(**{**produto.dict(), "id": db_produto.id})
            db_produto.img = produto.img
            # produtos_to_save.append(db_produto_to_update)
            produtos_to_save.append(db_produto)
            # await engine.save(db_produto)
        else:
            # prod = Produto(**{**produto.dict()})
            # produtos_to_save.append(prod)
            produtos_to_save.append(produto)
            # await engine.save(produto)
    await engine.save_all(produtos_to_save)
    return "db_updated"


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


@router.put("/api/produtos/images/")
async def read_produtos(produtos: List[Produto]):
# async def get_produtos(produtos: Optional[List[Produto]] = Query(None)):
    db_produto_list = []
    for produto in produtos:
        # db_produto = await engine.find_one(Produto,
        #                                    Produto.cod_referencia == produto.cod_referencia and
        #                                    Produto.nom_marca == produto.nom_marca and
        #                                    Produto.des_cor == produto.des_cor)
        db_produto = await engine.find_one(Produto,
                                           Produto.cod_referencia == produto.cod_referencia,
                                           Produto.nom_marca == produto.nom_marca,
                                           Produto.des_cor == produto.des_cor)
        if db_produto is not None:
            db_produto_list.append(db_produto)
        else:
            return
    return jsonable_encoder(db_produto_list)
    # return jsonable_encoder(db_produto)

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
