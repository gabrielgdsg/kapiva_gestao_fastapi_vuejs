"""
MongoDB models for Clientes dashboard.
PostgreSQL is read-only; computed/manual data stored in MongoDB.
"""
from datetime import datetime
from typing import List, Optional
from odmantic import Model, Field


class ClienteScore(Model):
    """Computed score and tags for a client."""
    cod_cliente: int
    nom_cliente: str
    score: int
    grade: str
    tags: List[str] = []
    total_parcelas: int = 0
    parcelas_pagas: int = 0
    pagas_com_atraso: int = 0
    parcelas_vencidas: int = 0
    mediana_dias_atraso: float = 0.0
    total_juros_pagos: float = 0.0
    saldo_em_aberto: float = 0.0
    recompra_pos_quita: bool = False
    ultima_quitacao: Optional[datetime] = None
    calculado_em: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "clientes_scores"


class ClienteWriteoff(Model):
    """Manual write-off flag set by user."""
    cod_cliente: int
    nom_cliente: str
    vlr_perdido: float
    motivo: Optional[str] = None
    registrado_em: datetime = Field(default_factory=datetime.utcnow)
    registrado_por: Optional[str] = None
    ativo: bool = True

    class Config:
        collection = "clientes_writeoffs"


class CampanhaConfig(Model):
    """Months with 60-day campaign active."""
    ano: int
    mes: int
    ativa: bool = True
    descricao: Optional[str] = None
    criado_em: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "campanhas_config"
