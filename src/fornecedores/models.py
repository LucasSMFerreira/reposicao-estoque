from dataclasses import dataclass


@dataclass(frozen=True)
class Fornecedor:
    id: str
    nome: str
    prazo_entrega_dias: int
    compra_minima: int = 1
    multiplo_compra: int = 1

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nome.strip():
            raise ValueError("Fornecedor precisa de id e nome.")
        if self.prazo_entrega_dias < 0:
            raise ValueError("Prazo de entrega não pode ser negativo.")
        if self.compra_minima < 1 or self.multiplo_compra < 1:
            raise ValueError("Compra mínima e múltiplo devem ser positivos.")
