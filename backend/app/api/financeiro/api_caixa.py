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
# import pandas as pd
# from ..utils import append_df_to_excel
from openpyxl import load_workbook


router = APIRouter()


@router.get("/api/financeiro/caixa/{data_caixa}")
async def get_caixa_table(data_caixa: str):
    data_caixa_datetime = datetime.fromisoformat(data_caixa)
    caixa = await engine.find_one(Caixa, Caixa.data_caixa == data_caixa_datetime)
    if caixa is None:
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
    print('/cartao')
    print(request)
    if request.method == 'GET':
        print('GET')
        data_caixa = datetime.strptime(data_caixa, '%Y-%m-%d').date()
        loj_cartao_value = get_cartao_vendas(data_caixa)
        payload = {'loj_cartao': loj_cartao_value}
        return payload


def get_cartao_dados(data_caixa_dateType):
    referenceDate = data_caixa_dateType.strftime('%Y') + data_caixa_dateType.strftime(
        '%m') + data_caixa_dateType.strftime('%d')
    print(referenceDate)
    url = "https://conciliation.stone.com.br/conciliation-file/v2.2/" + str(referenceDate)
    querystring = {"affiliationCode": "232084871"}
    headers = {
        'authorization': "Bearer 7b5fd261-3537-4a8a-bffc-0f2d5ec34501",
        'x-authorization-raw-data': "kapivacalcados2020emmovimento",
        'x-authorization-encrypted-data': "084da7241e06fa5612edf44693991cb5b1af63e118cf5fdaa27a1faaa866f04162eee459d7536bcdf00ff80e512aa3ad1d9f408b64d3a06b94791d484de09c95",
        'accept-encoding': "gzip"
    }
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        return response
    except:
        response = False
        return response
    # return response


def get_cartao_vendas(data_caixa_dateType):
    cartao_dec = 0
    response = get_cartao_dados(data_caixa_dateType)
    if response:
        if response.status_code == 200:
            obj = untangle.parse(response.text)
            transactions_count = len(obj.Conciliation.FinancialTransactions)
            if transactions_count > 0:
                for transaction in obj.Conciliation.FinancialTransactions.Transaction:
                    str_val = transaction.CapturedAmount.cdata
                    dec_val = Decimal(str_val)
                    cartao_dec = cartao_dec + dec_val
    cartao_str = str(cartao_dec)
    return cartao_str
