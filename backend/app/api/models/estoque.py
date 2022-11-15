from datetime import datetime
from typing import List
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal, Binary as binData
from pydantic import Extra
from pydantic import BaseModel


class ProdutoGrade(BaseModel):
# class ProdutoGrade(EmbeddedModel):
    P: int
    P_E: int
    M: int
    M_E: int
    G: int
    G_E: int

    class Config:
        allow_population_by_field_name = True
        extra = Extra.allow


class ProdutoMovto(BaseModel):
# class ProdutoMovto(EmbeddedModel):
    data_movto: datetime
    tipo_movto: int
    des_movto: str

    class Config:
        allow_population_by_field_name = True
        extra = Extra.allow
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        }


class ProdutoEstoque(Model):
    cod_grupo: int
    des_grupo: str
    cod_subgrupo: int
    des_subgrupo: str
    cod_produto: int
    des_produto: str
    vlr_custo_bruto: Decimal
    vlr_custo_aquis: Decimal
    vlr_venda1: Decimal
    cod_grade: int
    des_grade: str
    list_produto_grade: ProdutoGrade
    list_produto_movtos: List[ProdutoMovto]
    cod_cor: int
    dat_cadastro: datetime
    dat_ultcompra: datetime
    cod_fornecedor: int
    raz_fornecedor: str
    fan_fornecedor: str
    cod_marca: int
    cod_referencia: str
    nom_marca: str
    des_cor: str
    img: binData
    ratio: int

    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        }

class EstoqueProdutos(Model):
    datetime_atualizacao: datetime
    list_produtos: List[ProdutoEstoque]

    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S")
        }

