import json
from pathlib import Path

from src.estoque.models import Produto
from src.fornecedores.models import Fornecedor


def carregar_produtos(caminho: str | Path) -> list[Produto]:
    """Carrega produtos de um arquivo JSON com fornecedores por referência de ID."""
    with Path(caminho).open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    fornecedores = {
        item["id"]: Fornecedor(**item)
        for item in dados["fornecedores"]
    }
    produtos = []
    for item in dados["produtos"]:
        campos = item.copy()
        fornecedor_id = campos.pop("fornecedor_id")
        if fornecedor_id not in fornecedores:
            raise ValueError(f"Fornecedor desconhecido: {fornecedor_id}")
        produtos.append(Produto(fornecedor=fornecedores[fornecedor_id], **campos))
    return produtos
