"""Importação, exportação e registro local das decisões."""

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from src.estoque.models import Produto
from src.fornecedores.models import Fornecedor


COLUNAS = (
    "sku", "nome", "estoque_atual", "estoque_a_receber", "estoque_reservado",
    "consumo_medio_diario", "estoque_seguranca", "periodo_revisao_dias",
    "fornecedor_id", "fornecedor_nome", "prazo_entrega_dias",
    "compra_minima", "multiplo_compra",
)
COLUNAS_DECISOES = ("data_hora", "sku", "decisao", "quantidade", "motivo")


def salvar_json(caminho: str | Path, produtos: list[Produto]) -> None:
    fornecedores = {produto.fornecedor.id: produto.fornecedor for produto in produtos}
    dados = {
        "fornecedores": [asdict(f) for f in fornecedores.values()],
        "produtos": [
            {**asdict(p), "fornecedor_id": p.fornecedor.id}
            for p in produtos
        ],
    }
    for item in dados["produtos"]:
        del item["fornecedor"]
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def exportar_csv(caminho: str | Path, produtos: list[Produto]) -> None:
    with Path(caminho).open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, delimiter=";")
        escritor.writeheader()
        for p in produtos:
            escritor.writerow({
                "sku": p.sku, "nome": p.nome, "estoque_atual": p.estoque_atual,
                "estoque_a_receber": p.estoque_a_receber, "estoque_reservado": p.estoque_reservado,
                "consumo_medio_diario": p.consumo_medio_diario,
                "estoque_seguranca": p.estoque_seguranca,
                "periodo_revisao_dias": p.periodo_revisao_dias,
                "fornecedor_id": p.fornecedor.id, "fornecedor_nome": p.fornecedor.nome,
                "prazo_entrega_dias": p.fornecedor.prazo_entrega_dias,
                "compra_minima": p.fornecedor.compra_minima,
                "multiplo_compra": p.fornecedor.multiplo_compra,
            })


def importar_csv(caminho: str | Path) -> list[Produto]:
    produtos = []
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        ausentes = set(COLUNAS) - set(leitor.fieldnames or [])
        if ausentes:
            raise ValueError("Colunas ausentes no CSV: " + ", ".join(sorted(ausentes)))
        for numero, item in enumerate(leitor, start=2):
            try:
                fornecedor = Fornecedor(
                    item["fornecedor_id"], item["fornecedor_nome"],
                    int(item["prazo_entrega_dias"]), int(item["compra_minima"]),
                    int(item["multiplo_compra"]),
                )
                produtos.append(Produto(
                    sku=item["sku"], nome=item["nome"],
                    estoque_atual=int(item["estoque_atual"]),
                    estoque_a_receber=int(item["estoque_a_receber"]),
                    estoque_reservado=int(item["estoque_reservado"]),
                    consumo_medio_diario=float(item["consumo_medio_diario"].replace(",", ".")),
                    estoque_seguranca=int(item["estoque_seguranca"]),
                    periodo_revisao_dias=int(item["periodo_revisao_dias"]),
                    fornecedor=fornecedor,
                ))
            except (ValueError, TypeError, KeyError) as erro:
                raise ValueError(f"Linha {numero}: {erro}") from erro
    return produtos


def registrar_decisao(caminho: str | Path, sku: str, decisao: str, quantidade: int, motivo: str) -> None:
    if decisao not in {"Aceitar", "Ajustar", "Adiar"}:
        raise ValueError("Decisão inválida.")
    if quantidade < 0:
        raise ValueError("A quantidade não pode ser negativa.")
    destino = Path(caminho)
    novo = not destino.exists() or destino.stat().st_size == 0
    with destino.open("a", encoding="utf-8-sig" if novo else "utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        if novo:
            escritor.writerow(COLUNAS_DECISOES)
        escritor.writerow((datetime.now().astimezone().isoformat(timespec="seconds"), sku,
                          decisao, quantidade, motivo))
