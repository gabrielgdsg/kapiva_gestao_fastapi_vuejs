from datetime import datetime, date
from typing import List
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal, Binary as binData
from pydantic import Extra, BaseModel
from pydantic.schema import Optional


# class ProdutoGrade(BaseModel):
# # class ProdutoGrade(EmbeddedModel):
#     P: int
#     P_E: int
#     M: int
#     M_E: int
#     G: int
#     G_E: int
#
#     class Config:
#         allow_population_by_field_name = True
#         extra = Extra.allow


class ProdutoMovto(BaseModel):
# class ProdutoMovto(EmbeddedModel):
    cod_movto: Optional[int]
    cod_origem_movto: Optional[int]
    dat_movto: datetime
    tipo_movto: str
    des_movto: str
    id_movto: Optional[int]


    class Config:
        allow_population_by_field_name = True
        allow_mutation = True
        extra = Extra.allow
        json_encoders = {
            date: lambda v: datetime.strptime(str(v), "%Y-%m-%d").strftime("%d/%m/%Y"),
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        }

class ProdutoEstoquePostgres(Model):
    cod_grupo: Optional[int]
    des_grupo: Optional[str]
    cod_subgrupo: Optional[int]
    des_subgrupo: Optional[str]
    cod_produto: Optional[int]
    des_produto: Optional[str]
    cod_barra: Optional[int]
    cod_referencia: Optional[str]
    qtd: Optional[int]
    saldo_estoque: Optional[Decimal]
    vlr_custo_bruto: Optional[Decimal]
    vlr_custo_aquis: Optional[Decimal]
    vlr_venda1: Optional[Decimal]
    total: Optional[Decimal]
    cod_grade: Optional[int]
    des_grade: Optional[str]
    cod_tamanho: Optional[int]
    des_tamanho: Optional[str]
    cod_cor: Optional[int]
    des_cor: Optional[str]
    dat_cadastro: Optional[datetime]
    dat_ultcompra: Optional[datetime]
    dat_last_movto: Optional[datetime]
    cod_fornecedor:Optional[int]
    raz_fornecedor: Optional[str]
    fan_fornecedor: Optional[str]
    cod_marca: Optional[int]
    nom_marca: Optional[str]
    tipo_movto: Optional[str]
    qtd_movto: Optional[int]
    dat_movto: Optional[datetime]
    cod_movto: Optional[int]
    cod_origem_movto: Optional[int]
    des_movto: Optional[str]
    id_movto: Optional[int]
    img: Optional[binData]
    # img: binData = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=)',
    ratio: Optional[int]
    flag: Optional[bool]
    list_produto_movtos: Optional[List[ProdutoMovto]]


    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"),
            date: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        }


class ProdutoEstoqueMongo(Model):
    cod_grupo: Optional[int]
    des_grupo: Optional[str]
    cod_subgrupo: Optional[int]
    des_subgrupo: Optional[str]
    cod_produto: Optional[int]
    des_produto: Optional[str]
    # cod_barra: Optional[int]
    cod_referencia: Optional[str]
    # qtd: Optional[int]
    saldo_estoque: Optional[Decimal]
    vlr_custo_bruto: Optional[Decimal]
    vlr_custo_aquis: Optional[Decimal]
    vlr_venda1: Optional[Decimal]
    total: Optional[Decimal]
    cod_grade: Optional[int]
    des_grade: Optional[str]
    # cod_tamanho: Optional[int]
    # des_tamanho: Optional[str]
    cod_cor: Optional[int]
    des_cor: Optional[str]
    dat_cadastro: Optional[datetime]
    dat_ultcompra: Optional[datetime]
    dat_last_movto: Optional[datetime]
    cod_fornecedor:Optional[int]
    raz_fornecedor: Optional[str]
    fan_fornecedor: Optional[str]
    cod_marca: Optional[int]
    nom_marca: Optional[str]
    # tipo_movto: Optional[str]
    # qtd_movto: Optional[int]
    # dat_movto: Optional[datetime]
    # cod_movto: Optional[int]
    # cod_origem_movto: Optional[int]
    # des_movto: Optional[str]
    img: Optional[binData]
    # img: binData = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAMFBMVEXp7vG6vsG3u77s8fTCxsnn7O/f5OfFyczP09bM0dO8wMPk6ezY3eDd4uXR1tnJzdBvAX/cAAACVElEQVR4nO3b23KDIBRA0ShGU0n0//+2KmO94gWZ8Zxmr7fmwWEHJsJUHw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwO1MHHdn+L3rIoK6eshsNJ8kTaJI07fERPOO1Nc1vgQm2oiBTWJ+d8+CqV1heplLzMRNonED+4mg7L6p591FC+133/xCRNCtd3nL9BlxWP++MOaXFdEXFjZ7r8D9l45C8y6aG0cWtP/SUGhs2d8dA/ZfGgrzYX+TVqcTNRRO9l+fS5eSYzQs85psUcuzk6igcLoHPz2J8gvzWaH/JLS+95RfOD8o1p5CU5R7l5LkfKEp0mQ1UX7hsVXqDpRrifILD/3S9CfmlUQFhQfuFu0STTyJ8gsP3PH7GVxN1FC4t2sbBy4TNRTu7LyHJbqaqKFw+/Q0ncFloo7CjRPwMnCWqKXQZ75El4nKC9dmcJaou9AXOE5UXbi+RGeJygrz8Uf+GewSn9uXuplnWDZJ7d8f24F/s6iq0LYf9olbS3Q8i5oKrRu4S9ybwaQ/aCkqtP3I28QDgeoK7TBya/aXqL5COx67PTCD2grtdOwH+pQV2r0a7YVBgZoKwwIVFQYG6ikMDVRTGByopjD8ATcKb0UhhRTe77sKs2DV7FKSjId18TUEBYVyLhUThWfILHTDqmI85/2RWWjcE/bhP6OD7maT3h20MHsA47JC3PsW0wcwLhv9t0OOPOIkCn21y2bXXwlyylxiYMPk1SuCSmpfK8bNQvIrpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwNX4BCbAju9/X67UAAAAASUVORK5CYII=)',
    ratio: Optional[int]
    flag: Optional[bool]
    list_produto_movtos: Optional[List[ProdutoMovto]]=[]
    grade_estoque: Optional[dict] = {}

    class Config:
        json_encoders = {
            # datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"),
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")

        }



# class EstoqueProdutos(Model):
#     datetime_atualizacao: datetime
#     list_produtos: List[ProdutoEstoque]
#
#     class Config:
#         json_encoders = {
#             datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S")
#         }

