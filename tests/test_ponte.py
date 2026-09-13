import csv
import tempfile
import unittest
from pathlib import Path

from src.reposicao.ponte import compra_aprovada


class PonteTests(unittest.TestCase):
    def test_compra_aprovada_tem_id_estavel(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "decisoes.csv"
            with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                escritor.writerow(("data_hora", "sku", "decisao", "quantidade", "motivo"))
                escritor.writerow(("2026-09-13T10:00:00", "A", "Aceitar", 10, ""))
            primeira = compra_aprovada(caminho, "A")
            self.assertEqual(primeira, compra_aprovada(caminho, "A"))
            self.assertEqual(primeira[1], 10)
            with caminho.open("a", encoding="utf-8", newline="") as arquivo:
                csv.writer(arquivo, delimiter=";").writerow(("2026-09-13T10:01:00", "A", "Adiar", 0, ""))
            with self.assertRaises(ValueError):
                compra_aprovada(caminho, "A")


if __name__ == "__main__":
    unittest.main()
