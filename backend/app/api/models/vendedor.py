from datetime import datetime
from typing import List, Optional
from odmantic import Model, EmbeddedModel
from bson import Decimal128 as Decimal


class MetaMensal(EmbeddedModel):
    """Monthly target for a salesperson."""
    mes: int  # 1-12
    ano: int
    meta_1_2: Optional[Decimal] = None  # Target 1.2x
    meta_1_5: Optional[Decimal] = None  # Target 1.5x


class VendedorMetas(Model):
    """Sales targets (Metas) for a salesperson."""
    cod_vendedor: int
    nom_vendedor: Optional[str] = None
    metas_mensais: List[MetaMensal] = []
    ativo: bool = True
    data_criacao: datetime = datetime.now()
    data_atualizacao: datetime = datetime.now()


class VendedorGrupo(Model):
    """Group of selected active salespersons."""
    nome_grupo: Optional[str] = None
    vendedores_selecionados: List[int] = []  # List of cod_vendedor
    data_criacao: datetime = datetime.now()
    data_atualizacao: datetime = datetime.now()


class VendedorTipo(EmbeddedModel):
    """Seller type assignment (Calçado or Roupa)."""
    cod_vendedor: int
    tipo: str  # "Calçado" or "Roupa"
    ano: int  # Year this assignment is valid for


class VendedorConfigMetas(Model):
    """Configuration for Metas calculation."""
    ano: int
    mes: int
    vendedores_tipo: List[VendedorTipo] = []  # Calçado/Roupa assignments
    vendedores_ativos: List[int] = []  # Active sellers for this year
    margem_padrao: Decimal = Decimal("0.10")  # Default 10% margin
    meta_1: Decimal = Decimal("1.2")  # Meta 1 (formerly 1.2x)
    meta_2: Decimal = Decimal("1.5")  # Meta 2 (formerly 1.5x)
    meta_3: Optional[Decimal] = None  # Meta 3 (optional)
    meta_4: Optional[Decimal] = None  # Meta 4 (optional)
    meta_5: Optional[Decimal] = None  # Meta 5 (optional)
    metas_liberadas: bool = False  # If True, vendedores can see their goals in the painel
    data_criacao: datetime = datetime.now()
    data_atualizacao: datetime = datetime.now()


class VendedorSlug(Model):
    """Unique URL slug for seller dashboard access.
    e.g. /painel/vanessa34567 - name + 5 digit random number.
    """
    cod_vendedor: int
    nom_vendedor: str
    slug: str  # e.g. "vanessa34567"
    ativo: bool = True
    data_criacao: datetime = datetime.now()
    data_atualizacao: datetime = datetime.now()
