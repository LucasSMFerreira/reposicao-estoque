import csv
import tempfile
import unittest
from pathlib import Path

from src.database.arquivos import exportar_csv, importar_csv, registrar_decisao, salvar_json
from src.database.repository import carregar_produtos
from src.estoque.models import Produto
from src.fornecedores.models import Fornecedor
from src.interface.painel import explicar, situacao


class ControleTests(unittest.TestCase):
    def setUp(self) -> None:
        fornecedor = Fornecedor("FOR-1", "Teste", 5, 10, 5)
        self.produtos = [
            Produto("A", "Produto A", 7, 4, 5, fornecedor),
            Produto("B", "Produto B", 30, 4, 5, fornecedor),
            Produto("C", "Produto C", 80, 4, 5, fornecedor),
        ]

    def test_prioridades_e_explicacao(self) -> None:
        self.assertEqual([situacao(p) for p in self.produtos],
                         ["Comprar agora", "Comprar em breve", "OK"])
        self.assertIn("comprar 50", explicar(self.produtos[0]))

    def test_csv_e_json_podem_ser_reabertos(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            csv_path = Path(pasta) / "produtos.csv"
            json_path = Path(pasta) / "produtos.json"
            exportar_csv(csv_path, self.produtos)
            importados = importar_csv(csv_path)
            self.assertEqual([p.sku for p in importados], ["A", "B", "C"])
            salvar_json(json_path, importados)
            self.assertEqual(carregar_produtos(json_path), importados)

    def test_decisao_fica_registrada(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "decisoes.csv"
            registrar_decisao(caminho, "A", "Ajustar", 30, "pedido parcial")
            with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
                linhas = list(csv.DictReader(arquivo, delimiter=";"))
            self.assertEqual(linhas[0]["quantidade"], "30")
            self.assertEqual(linhas[0]["motivo"], "pedido parcial")


if __name__ == "__main__":
    unittest.main()
