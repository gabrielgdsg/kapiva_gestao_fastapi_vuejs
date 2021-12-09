from datetime import datetime, date
from typing import List
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal, Binary as binData


class LevantamentoEstoque(Model):
    cod_grupo: int
    des_grupo: str
    cod_subgrupo: int
    des_subgrupo: str
    cod_produto: int
    des_produto: str
    cod_barra: int
    cod_referencia: str
    qtd: int
    saldo_estoque: Decimal
    vlr_custo_bruto: Decimal
    vlr_custo_aquis: Decimal
    vlr_venda1: Decimal
    total: Decimal
    cod_grade: int
    des_grade: str
    cod_tamanho: int
    des_tamanho: str
    cod_cor: int
    des_cor: str
    dat_cadastro: datetime
    dat_alteracao: date
    dat_emissao: date
    dat_lancamento: date
    dat_saida: date
    cod_fornecedor: int
    raz_fornecedor: str
    fan_fornecedor: str
    cod_marca: int
    nom_marca: str
    tipo_movto: str
    qtd_movto: int
    data_movto: date
    cod_movto: int
    cod_origem_movto: int


    class Config:
        json_encoders = {
            date: lambda v: datetime.strptime(str(v), "%Y-%m-%d").strftime("%d/%m/%Y"),
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m/%Y")
            # Decimal: lambda v: v.to_decimal()
        }


class MarcaFornecedor(Model):
    cod_marca: int
    nom_marca: str
    cod_fornecedor: int
    raz_fornecedor: str
    fan_fornecedor: str


class Fornecedor(EmbeddedModel):
    cod_fornecedor: int
    raz_fornecedor: str
    fan_fornecedor: str


class Marcas(Model):
    cod_marca: int
    nom_marca: str
    fornecedores: List[Fornecedor]


class Produto(Model):
    # cod_grupo: int
    # des_grupo: str
    # cod_subgrupo: int
    # des_subgrupo: str
    # cod_produto: int
    des_produto: str
    # vlr_custo_bruto: Decimal
    # vlr_custo_aquis: Decimal
    # vlr_venda1: Decimal
    # cod_grade: int
    # des_grade: str
    # cod_cor: int
    # dat_cadastro: datetime
    # dat_alteracao: date
    # dat_emissao: date
    # dat_lancamento: date
    # cod_fornecedor: int
    # raz_fornecedor: str
    # fan_fornecedor: str
    # cod_marca: int
    cod_referencia: str
    nom_marca: str
    des_cor: str
    # img: str
    img: binData