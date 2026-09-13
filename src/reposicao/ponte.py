"""Envia uma compra aprovada à API local de Contas a Pagar."""

import csv
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.estoque.models import Produto


def compra_aprovada(caminho_decisoes: str | Path, sku: str) -> tuple[str, int]:
    """Devolve um ID estável e a quantidade da última decisão do SKU."""
    with Path(caminho_decisoes).open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))
    encontrada = next(((indice, linha) for indice, linha in reversed(list(enumerate(linhas, start=1)))
                      if linha.get("sku") == sku), None)
    if encontrada is None:
        raise ValueError("Registre primeiro a compra como Aceitar ou Ajustar.")
    indice, linha = encontrada
    if linha.get("decisao") not in {"Aceitar", "Ajustar"}:
        raise ValueError("A última decisão deste produto não aprova a compra.")
    quantidade = int(linha["quantidade"])
    if quantidade <= 0:
        raise ValueError("A compra aprovada precisa ter quantidade positiva.")
    chave = f"{sku}|{linha['data_hora']}|{indice}|{quantidade}".encode("utf-8")
    pedido_id = "REP-" + hashlib.sha256(chave).hexdigest()[:16].upper()
    return pedido_id, quantidade


def enviar_compra(
    produto: Produto, pedido_id: str, quantidade: int, valor_unitario: str,
    vencimento: str, url_base: str = "http://127.0.0.1:8765",
) -> dict[str, object]:
    try:
        preco = Decimal(valor_unitario.strip().replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError("Preço unitário inválido.") from erro
    if not preco.is_finite() or preco <= 0 or preco != preco.quantize(Decimal("0.01")):
        raise ValueError("Informe um preço positivo com até duas casas decimais.")
    if quantidade <= 0:
        raise ValueError("Quantidade inválida.")
    date.fromisoformat(vencimento)
    corpo = json.dumps({
        "pedido_id": pedido_id, "sku": produto.sku, "produto": produto.nome,
        "fornecedor": produto.fornecedor.nome, "quantidade": quantidade,
        "valor_unitario": str(preco), "vencimento": vencimento,
    }).encode("utf-8")
    requisicao = Request(url_base.rstrip("/") + "/api/v1/pedidos-reposicao", corpo,
                         {"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(requisicao, timeout=5) as resposta:
            return json.load(resposta)
    except HTTPError as erro:
        try:
            detalhe = json.load(erro).get("erro", str(erro))
        except (ValueError, AttributeError):
            detalhe = str(erro)
        raise ValueError(f"Contas a Pagar recusou a compra: {detalhe}") from erro
    except URLError as erro:
        raise ConnectionError("Ative a ponte em Contas a Pagar e tente novamente.") from erro
