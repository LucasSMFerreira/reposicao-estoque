import unittest
from pathlib import Path

from src.database.repository import carregar_produtos
from src.estoque.models import Produto
from src.fornecedores.models import Fornecedor
from src.reposicao.service import (
    calcular_ponto_reposicao,
    calcular_quantidade_sugerida,
    precisa_repor,
)


class ReposicaoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fornecedor = Fornecedor("F1", "Fornecedor", 5, compra_minima=10, multiplo_compra=5)

    def produto(self, estoque: int, **campos: int) -> Produto:
        return Produto(
            sku="ABC",
            nome="Exemplo",
            estoque_atual=estoque,
            consumo_medio_diario=4,
            estoque_seguranca=5,
            fornecedor=self.fornecedor,
            **campos,
        )

    def test_ponto_e_quantidade_arredondada(self) -> None:
        produto = self.produto(7)
        self.assertEqual(calcular_ponto_reposicao(produto), 25)
        self.assertTrue(precisa_repor(produto))
        self.assertEqual(calcular_quantidade_sugerida(produto), 50)

    def test_sem_reposicao_acima_do_ponto(self) -> None:
        produto = self.produto(40)
        self.assertFalse(precisa_repor(produto))
        self.assertEqual(calcular_quantidade_sugerida(produto), 0)

    def test_estoque_a_receber_e_reservado(self) -> None:
        produto = self.produto(25, estoque_a_receber=5, estoque_reservado=5)
        self.assertEqual(produto.estoque_disponivel, 25)
        self.assertTrue(precisa_repor(produto))
        self.assertEqual(calcular_quantidade_sugerida(produto), 30)

    def test_compra_minima(self) -> None:
        fornecedor = Fornecedor("F2", "Outro", 0, compra_minima=12, multiplo_compra=5)
        produto = Produto("ABC", "Exemplo", 0, 0, 1, fornecedor)
        self.assertEqual(calcular_quantidade_sugerida(produto), 15)

    def test_dados_de_exemplo(self) -> None:
        caminho = Path(__file__).resolve().parents[1] / "data" / "produtos.json"
        produtos = carregar_produtos(caminho)
        self.assertEqual(len(produtos), 3)
        self.assertEqual(produtos[0].sku, "MOUSE-001")

    def test_valores_negativos_sao_invalidos(self) -> None:
        with self.assertRaises(ValueError):
            self.produto(-1)


if __name__ == "__main__":
    unittest.main()
