from dataclasses import dataclass
from math import ceil

from src.estoque.models import Produto


@dataclass(frozen=True)
class SugestaoReposicao:
    sku: str
    ponto_reposicao: int
    estoque_disponivel: int
    precisa_repor: bool
    quantidade_sugerida: int


def calcular_ponto_reposicao(produto: Produto) -> int:
    demanda_no_prazo = produto.consumo_medio_diario * produto.fornecedor.prazo_entrega_dias
    return ceil(demanda_no_prazo + produto.estoque_seguranca)


def precisa_repor(produto: Produto) -> bool:
    return produto.estoque_disponivel <= calcular_ponto_reposicao(produto)


def calcular_quantidade_sugerida(produto: Produto) -> int:
    if not precisa_repor(produto):
        return 0

    dias_cobertura = produto.fornecedor.prazo_entrega_dias + produto.periodo_revisao_dias
    estoque_alvo = ceil(produto.consumo_medio_diario * dias_cobertura + produto.estoque_seguranca)
    necessidade = max(0, estoque_alvo - produto.estoque_disponivel)
    if necessidade == 0:
        return 0

    fornecedor = produto.fornecedor
    quantidade = max(necessidade, fornecedor.compra_minima)
    return ceil(quantidade / fornecedor.multiplo_compra) * fornecedor.multiplo_compra


def analisar_produto(produto: Produto) -> SugestaoReposicao:
    return SugestaoReposicao(
        sku=produto.sku,
        ponto_reposicao=calcular_ponto_reposicao(produto),
        estoque_disponivel=produto.estoque_disponivel,
        precisa_repor=precisa_repor(produto),
        quantidade_sugerida=calcular_quantidade_sugerida(produto),
    )
