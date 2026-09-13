import argparse
from pathlib import Path

from src.database.repository import carregar_produtos
from src.reposicao.service import analisar_produto


ARQUIVO_EXEMPLO = Path(__file__).parent / "data" / "produtos.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Sugestões simples de reposição de estoque")
    parser.add_argument("--dados", type=Path, default=ARQUIVO_EXEMPLO, help="Arquivo JSON de entrada")
    parser.add_argument("--cli", action="store_true", help="Mostra o resultado no terminal")
    argumentos = parser.parse_args()

    if not argumentos.cli:
        try:
            from src.interface.painel import iniciar_interface
            iniciar_interface(argumentos.dados)
        except ImportError as erro:
            parser.exit(1, f"Tkinter indisponível: {erro}. Use --cli.\n")
        return

    try:
        produtos = carregar_produtos(argumentos.dados)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        parser.exit(1, f"Erro ao carregar os dados: {erro}\n")

    for produto in produtos:
        sugestao = analisar_produto(produto)
        situacao = "REPOR" if sugestao.precisa_repor else "OK"
        print(
            f"{produto.sku} | {produto.nome} | {situacao} | "
            f"disponível: {sugestao.estoque_disponivel} | "
            f"ponto: {sugestao.ponto_reposicao} | "
            f"comprar: {sugestao.quantidade_sugerida}"
        )


if __name__ == "__main__":
    main()
