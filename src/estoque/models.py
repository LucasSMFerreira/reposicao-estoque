from dataclasses import dataclass
from math import isfinite

from src.fornecedores.models import Fornecedor


@dataclass(frozen=True)
class Produto:
    sku: str
    nome: str
    estoque_atual: int
    consumo_medio_diario: float
    estoque_seguranca: int
    fornecedor: Fornecedor
    periodo_revisao_dias: int = 7
    estoque_a_receber: int = 0
    estoque_reservado: int = 0

    def __post_init__(self) -> None:
        if not self.sku.strip() or not self.nome.strip():
            raise ValueError("Produto precisa de SKU e nome.")
        if any(valor < 0 for valor in (
            self.estoque_atual,
            self.consumo_medio_diario,
            self.estoque_seguranca,
            self.periodo_revisao_dias,
            self.estoque_a_receber,
            self.estoque_reservado,
        )):
            raise ValueError("Valores de estoque, consumo e período não podem ser negativos.")
        if not isfinite(self.consumo_medio_diario):
            raise ValueError("Consumo médio diário precisa ser um número finito.")

    @property
    def estoque_disponivel(self) -> int:
        return self.estoque_atual + self.estoque_a_receber - self.estoque_reservado
