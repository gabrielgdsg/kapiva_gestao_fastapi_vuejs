from datetime import datetime
from typing import List
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal


class LojSangria(EmbeddedModel):
    item: str
    valor: Decimal


class LojOutrasEntradas(EmbeddedModel):
    item: str
    valor: Decimal


class LojCartao(EmbeddedModel):
    item: str
    valor: Decimal


class LojSuprimento(EmbeddedModel):
    item: str
    valor: Decimal


class LojTroco(EmbeddedModel):
    item: str
    valor: Decimal


class LojTotal(EmbeddedModel):
    item: str
    valor: Decimal


class SistTroco(EmbeddedModel):
    item: str
    valor: Decimal


class SistPos(EmbeddedModel):
    item: str
    valor: Decimal


class SistDinheiro(EmbeddedModel):
    item: str
    valor: Decimal

class SistTotal(EmbeddedModel):
    item: str
    valor: Decimal


class ResCaixa(EmbeddedModel):
    item: str
    valor: Decimal


class Caixa(Model):
    data_caixa: datetime
    loj_sangria_list: List[LojSangria]
    loj_outras_entradas_list: List[LojOutrasEntradas]
    loj_cartao: LojCartao
    loj_suprimento: LojSuprimento
    loj_troco: LojTroco
    loj_total: LojTotal
    sist_troco: SistTroco
    sist_pos: SistPos
    sist_dinheiro: SistDinheiro
    sist_total: SistTotal
    res_caixa: ResCaixa

    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        }


class User(Model):
    data_caixa: datetime
    loj_sangria_list: List[LojSangria]
    loj_outras_entradas_list: List[LojOutrasEntradas]
    loj_cartao: LojCartao
    loj_suprimento: LojSuprimento
    loj_troco: LojTroco
    sist_troco: SistTroco
    sist_pos: SistPos
    sist_dinheiro: SistDinheiro
    sist_total: SistTotal
    res_caixa: ResCaixa

    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        }