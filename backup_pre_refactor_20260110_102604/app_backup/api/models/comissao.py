from datetime import datetime
from typing import List, Optional
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal


class ComissaoVendedor(EmbeddedModel):
    cod_vendedor:  Optional[int]
    nom_vendedor: Optional[str]
    base_calc_comissao: Optional[Decimal]
    vlr_comissao: Optional[Decimal]
    cred_dev: Optional[Decimal]
    # percent_comissao: Decimal
    data_ini: Optional[datetime]
    data_fim: Optional[datetime]


class ComissaoDia(Model):
    data_comissao: datetime
    comissao_vendedores: List[ComissaoVendedor]
    # comissao_total: Decimal

    class Config:
        json_encoders = {
            datetime: lambda v: datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
            # Decimal: lambda v: v.to_decimal()
        }

