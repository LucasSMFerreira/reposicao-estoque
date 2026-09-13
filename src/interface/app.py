import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.database.repository import carregar_produtos
from src.estoque.models import Produto
from src.fornecedores.models import Fornecedor
from src.reposicao.service import analisar_produto


CAMPOS = (
    ("sku", "SKU", "text"),
    ("nome", "Produto", "text"),
    ("estoque_atual", "Estoque atual", "int"),
    ("estoque_a_receber", "A receber", "int"),
    ("estoque_reservado", "Reservado", "int"),
    ("consumo_medio_diario", "Consumo médio/dia", "float"),
    ("estoque_seguranca", "Estoque de segurança", "int"),
    ("prazo_entrega_dias", "Prazo de entrega (dias)", "int"),
    ("periodo_revisao_dias", "Revisão (dias)", "int"),
    ("compra_minima", "Compra mínima", "int"),
    ("multiplo_compra", "Múltiplo de compra", "int"),
)


def criar_produto_dos_campos(valores: dict[str, str]) -> Produto:
    """Converte e valida os valores digitados, sem depender da janela gráfica."""
    convertidos: dict[str, str | int | float] = {}
    for chave, rotulo, tipo in CAMPOS:
        bruto = valores[chave].strip()
        if not bruto:
            raise ValueError(f"Preencha o campo: {rotulo}.")
        try:
            if tipo == "int":
                convertidos[chave] = int(bruto)
            elif tipo == "float":
                convertidos[chave] = float(bruto.replace(",", "."))
            else:
                convertidos[chave] = bruto
        except ValueError as erro:
            raise ValueError(f"Valor inválido em {rotulo}: {bruto!r}.") from erro

    fornecedor = Fornecedor(
        id="MANUAL",
        nome="Fornecedor informado",
        prazo_entrega_dias=convertidos["prazo_entrega_dias"],
        compra_minima=convertidos["compra_minima"],
        multiplo_compra=convertidos["multiplo_compra"],
    )
    return Produto(
        sku=convertidos["sku"],
        nome=convertidos["nome"],
        estoque_atual=convertidos["estoque_atual"],
        estoque_a_receber=convertidos["estoque_a_receber"],
        estoque_reservado=convertidos["estoque_reservado"],
        consumo_medio_diario=convertidos["consumo_medio_diario"],
        estoque_seguranca=convertidos["estoque_seguranca"],
        periodo_revisao_dias=convertidos["periodo_revisao_dias"],
        fornecedor=fornecedor,
    )


class Aplicacao(tk.Tk):
    def __init__(self, caminho_dados: Path) -> None:
        super().__init__()
        self.title("Reposição Automática de Estoque — V2")
        self.geometry("890x620")
        self.minsize(760, 560)
        self.produtos: list[Produto] = []
        self.variaveis = {chave: tk.StringVar() for chave, _, _ in CAMPOS}
        self.resultado = tk.StringVar(value="Selecione um produto ou preencha os campos para verificar.")
        self._montar_tela()
        self._carregar(caminho_dados)

    def _montar_tela(self) -> None:
        quadro = ttk.Frame(self, padding=16)
        quadro.pack(fill="both", expand=True)
        ttk.Label(quadro, text="Verificação de reposição", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(quadro, text="Escolha um exemplo ou digite os dados e clique em Verificar.").pack(anchor="w", pady=(0, 12))

        barra = ttk.Frame(quadro)
        barra.pack(fill="x", pady=(0, 10))
        ttk.Button(barra, text="Abrir JSON...", command=self._abrir_arquivo).pack(side="left")
        ttk.Label(barra, text="   Produto de exemplo:").pack(side="left")
        self.seletor = ttk.Combobox(barra, state="readonly", width=42)
        self.seletor.pack(side="left", padx=6)
        self.seletor.bind("<<ComboboxSelected>>", self._selecionar)

        campos = ttk.LabelFrame(quadro, text="Dados para o cálculo", padding=12)
        campos.pack(fill="x")
        for indice, (chave, rotulo, _) in enumerate(CAMPOS):
            linha, coluna = divmod(indice, 2)
            ttk.Label(campos, text=rotulo).grid(row=linha, column=coluna * 2, sticky="w", padx=(0, 8), pady=5)
            ttk.Entry(campos, textvariable=self.variaveis[chave], width=23).grid(
                row=linha, column=coluna * 2 + 1, sticky="ew", padx=(0, 24), pady=5
            )
        campos.columnconfigure(1, weight=1)
        campos.columnconfigure(3, weight=1)

        ttk.Button(quadro, text="Verificar reposição", command=self._verificar).pack(anchor="w", pady=14)
        ttk.Label(quadro, textvariable=self.resultado, font=("Segoe UI", 11), wraplength=820,
                  justify="left").pack(anchor="w", fill="x")
        ttk.Label(quadro, text="Sugestão informativa: nenhum pedido é enviado automaticamente.").pack(
            side="bottom", anchor="w", pady=(12, 0)
        )

    def _carregar(self, caminho: Path) -> None:
        try:
            self.produtos = carregar_produtos(caminho)
        except (OSError, ValueError, KeyError, TypeError) as erro:
            messagebox.showerror("Erro ao abrir dados", str(erro))
            return
        self.seletor["values"] = [f"{produto.sku} — {produto.nome}" for produto in self.produtos]
        if self.produtos:
            self.seletor.current(0)
            self._selecionar()

    def _abrir_arquivo(self) -> None:
        caminho = filedialog.askopenfilename(title="Abrir dados de produtos", filetypes=[("JSON", "*.json")])
        if caminho:
            self._carregar(Path(caminho))

    def _selecionar(self, _evento: object = None) -> None:
        indice = self.seletor.current()
        if indice < 0:
            return
        produto = self.produtos[indice]
        valores = {
            "sku": produto.sku,
            "nome": produto.nome,
            "estoque_atual": produto.estoque_atual,
            "estoque_a_receber": produto.estoque_a_receber,
            "estoque_reservado": produto.estoque_reservado,
            "consumo_medio_diario": produto.consumo_medio_diario,
            "estoque_seguranca": produto.estoque_seguranca,
            "prazo_entrega_dias": produto.fornecedor.prazo_entrega_dias,
            "periodo_revisao_dias": produto.periodo_revisao_dias,
            "compra_minima": produto.fornecedor.compra_minima,
            "multiplo_compra": produto.fornecedor.multiplo_compra,
        }
        for chave, valor in valores.items():
            self.variaveis[chave].set(str(valor))
        self._verificar()

    def _verificar(self) -> None:
        try:
            produto = criar_produto_dos_campos({chave: var.get() for chave, var in self.variaveis.items()})
            sugestao = analisar_produto(produto)
        except (ValueError, OverflowError) as erro:
            messagebox.showerror("Dados inválidos", str(erro))
            return
        situacao = "REPOR" if sugestao.precisa_repor else "ESTOQUE OK"
        self.resultado.set(
            f"{situacao}  |  Disponível: {sugestao.estoque_disponivel}  |  "
            f"Ponto de reposição: {sugestao.ponto_reposicao}  |  "
            f"Quantidade sugerida: {sugestao.quantidade_sugerida} unidade(s)"
        )


def iniciar_interface(caminho_dados: Path) -> None:
    Aplicacao(caminho_dados).mainloop()
