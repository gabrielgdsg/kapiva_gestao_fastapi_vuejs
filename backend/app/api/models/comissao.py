from datetime import datetime
from typing import List
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal


class ComissaoVendedor(EmbeddedModel):
    cod_vendedor: int
    nom_vendedor: str
    base_calc_comissao: Decimal
    vlr_comissao: Decimal
    cred_dev: Decimal
    # percent_comissao: Decimal
    data_ini: datetime
    data_fim: datetime


class ComissaoDia(Model):
    data_comissao: datetime
    comissao_vendedores: List[ComissaoVendedor]
    # comissao_total: Decimal

    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
            # Decimal: lambda v: v.to_decimal()
        }

