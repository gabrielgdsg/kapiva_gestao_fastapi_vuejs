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


class ComissaoAlteracaoLog(EmbeddedModel):
    """Log entry for commission changes."""
    data_alteracao: datetime
    base_calc_anterior: Optional[Decimal] = None
    base_calc_novo: Optional[Decimal] = None
    valor_anterior: Decimal
    valor_novo: Decimal
    observacao: Optional[str] = None
    usuario: Optional[str] = None


class ComissaoEditada(Model):
    """Stores edited commission values (MongoDB only, never touches PostgreSQL)."""
    data_comissao: datetime
    cod_vendedor: int
    nom_vendedor: Optional[str] = None
    base_calc_comissao_original: Optional[Decimal] = None  # Original base_calc from PostgreSQL
    base_calc_comissao_editado: Optional[Decimal] = None  # Edited base_calc (MongoDB only)
    vlr_comissao_original: Decimal  # Original value from PostgreSQL
    vlr_comissao_editado: Decimal  # Edited value (MongoDB only)
    base_calc_comissao: Optional[Decimal] = None  # Keep for reference
    cred_dev: Optional[Decimal] = None
    observacao: Optional[str] = None  # Current observation
    data_ini: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    alteracoes: List[ComissaoAlteracaoLog] = []  # History of changes
    data_criacao: datetime = datetime.now()
    data_atualizacao: datetime = datetime.now()

