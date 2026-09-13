import unittest
from math import nan

from src.estoque.models import Produto
from src.fornecedores.models import Fornecedor
from src.interface.app import criar_produto_dos_campos
from src.reposicao.service import calcular_quantidade_sugerida


class InterfaceTests(unittest.TestCase):
    def test_campos_da_interface(self) -> None:
        valores = {
            "sku": "ABC", "nome": "Exemplo", "estoque_atual": "7",
            "estoque_a_receber": "0", "estoque_reservado": "0",
            "consumo_medio_diario": "4,0", "estoque_seguranca": "5",
            "prazo_entrega_dias": "5", "periodo_revisao_dias": "7",
            "compra_minima": "10", "multiplo_compra": "5",
        }
        self.assertEqual(calcular_quantidade_sugerida(criar_produto_dos_campos(valores)), 50)
        valores["estoque_atual"] = "texto"
        with self.assertRaises(ValueError):
            criar_produto_dos_campos(valores)

    def test_consumo_nan_e_invalido(self) -> None:
        fornecedor = Fornecedor("F", "Fornecedor", 2)
        with self.assertRaises(ValueError):
            Produto("ABC", "Exemplo", 1, nan, 1, fornecedor)


if __name__ == "__main__":
    unittest.main()
