"""Painel simples para acompanhar e registrar sugestões de reposição."""

import tkinter as tk
from dataclasses import replace
from math import ceil
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from src.database.arquivos import exportar_csv, importar_csv, registrar_decisao, salvar_json
from src.database.repository import carregar_produtos
from src.estoque.models import Produto
from src.interface.app import CAMPOS, criar_produto_dos_campos
from src.reposicao.service import analisar_produto
from src.reposicao.ponte import compra_aprovada, enviar_compra


AJUDA = {
    "estoque_seguranca": "Reserva para imprevistos no consumo ou na entrega.",
    "prazo_entrega_dias": "Dias entre a compra e a chegada do produto.",
    "multiplo_compra": "Lote exigido pelo fornecedor (ex.: caixas de 5).",
    "periodo_revisao_dias": "Dias até a próxima conferência do estoque.",
}


def situacao(produto: Produto) -> str:
    disponivel = produto.estoque_disponivel
    ponto = analisar_produto(produto).ponto_reposicao
    if disponivel <= ponto:
        return "Comprar agora"
    limite_proximo = ponto + ceil(produto.consumo_medio_diario * produto.periodo_revisao_dias)
    return "Comprar em breve" if disponivel <= limite_proximo else "OK"


def explicar(produto: Produto) -> str:
    analise = analisar_produto(produto)
    return (
        f"Há {analise.estoque_disponivel} unidade(s) disponíveis. "
        f"O ponto de reposição é {analise.ponto_reposicao}. "
        f"Sugestão: comprar {analise.quantidade_sugerida} unidade(s). "
        f"Prazo do fornecedor: {produto.fornecedor.prazo_entrega_dias} dia(s)."
    )


class Painel(tk.Tk):
    def __init__(self, caminho_dados: Path) -> None:
        super().__init__()
        self.title("Controle de reposição de estoque")
        self.geometry("1080x760")
        self.minsize(860, 650)
        self.caminho_dados = caminho_dados
        self.produtos: list[Produto] = []
        self.selecionado: str | None = None
        self.alteracoes_pendentes = False
        self.busca = tk.StringVar()
        self.filtro = tk.StringVar(value="Todos")
        self.resumo = tk.StringVar(value="Selecione um produto para ver a sugestão.")
        self.status = tk.StringVar(value="")
        self.campos = {chave: tk.StringVar() for chave, _, _ in CAMPOS}
        self._montar()
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self._abrir(caminho_dados)

    def _montar(self) -> None:
        raiz = ttk.Frame(self, padding=14)
        raiz.pack(fill="both", expand=True)
        ttk.Label(raiz, text="Controle de reposição", font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(raiz, text="Veja o que precisa de atenção, confira os dados e registre sua decisão.").pack(anchor="w", pady=(0, 10))

        arquivos = ttk.Frame(raiz)
        arquivos.pack(fill="x", pady=(0, 9))
        for texto, acao in (
            ("Abrir JSON", self._abrir_json), ("Importar CSV", self._importar_csv),
            ("Salvar JSON", self._salvar_json), ("Exportar CSV", self._exportar_csv),
        ):
            ttk.Button(arquivos, text=texto, command=acao).pack(side="left", padx=(0, 7))

        filtros = ttk.Frame(raiz)
        filtros.pack(fill="x", pady=(0, 6))
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        ttk.Entry(filtros, textvariable=self.busca, width=29).pack(side="left", padx=(6, 15))
        self.busca.trace_add("write", lambda *_: self._atualizar_lista())
        ttk.Label(filtros, text="Situação:").pack(side="left")
        seletor = ttk.Combobox(filtros, textvariable=self.filtro, state="readonly", width=20,
                               values=("Todos", "Comprar agora", "Comprar em breve", "OK"))
        seletor.pack(side="left", padx=6)
        seletor.bind("<<ComboboxSelected>>", lambda _: self._atualizar_lista())

        colunas = ("situacao", "sku", "nome", "disponivel", "ponto", "comprar")
        self.lista = ttk.Treeview(raiz, columns=colunas, show="headings", height=10, selectmode="browse")
        for chave, titulo, largura in (
            ("situacao", "Situação", 135), ("sku", "SKU", 115), ("nome", "Produto", 280),
            ("disponivel", "Disponível", 85), ("ponto", "Ponto", 70), ("comprar", "Comprar", 85),
        ):
            self.lista.heading(chave, text=titulo)
            self.lista.column(chave, width=largura, stretch=chave == "nome")
        self.lista.tag_configure("agora", foreground="#a32323")
        self.lista.tag_configure("breve", foreground="#8a5a00")
        self.lista.pack(fill="both", expand=True)
        self.lista.bind("<<TreeviewSelect>>", self._selecionar)

        ttk.Label(raiz, textvariable=self.resumo, font=("Segoe UI", 10, "bold"),
                  wraplength=1000).pack(anchor="w", pady=(10, 5))
        editor = ttk.LabelFrame(raiz, text="Dados do produto — edite e clique em Salvar produto", padding=9)
        editor.pack(fill="x")
        for indice, (chave, rotulo, _) in enumerate(CAMPOS):
            linha, coluna = divmod(indice, 3)
            ttk.Label(editor, text=rotulo).grid(row=linha * 2, column=coluna, sticky="w", padx=5)
            ttk.Entry(editor, textvariable=self.campos[chave], width=23).grid(
                row=linha * 2 + 1, column=coluna, sticky="ew", padx=5, pady=(0, 4)
            )
            editor.columnconfigure(coluna, weight=1)
        ttk.Label(editor, text="Segurança = reserva  •  Prazo = dias para chegar  •  Múltiplo = lote do fornecedor",
                  foreground="#555555").grid(row=8, column=0, columnspan=3, sticky="w", pady=4)

        acoes = ttk.Frame(raiz)
        acoes.pack(fill="x", pady=8)
        for texto, acao in (
            ("Novo produto", self._novo), ("Salvar produto", self._salvar_produto),
            ("Aceitar sugestão", lambda: self._decidir("Aceitar")),
            ("Ajustar", lambda: self._decidir("Ajustar")),
            ("Adiar", lambda: self._decidir("Adiar")),
            ("Enviar para Contas a Pagar", self._enviar_compra),
        ):
            ttk.Button(acoes, text=texto, command=acao).pack(side="left", padx=(0, 7))
        ttk.Label(raiz, textvariable=self.status, foreground="#555555").pack(anchor="w")

    def _fechar(self) -> None:
        if self.alteracoes_pendentes and not messagebox.askyesno("Alterações não salvas", "Fechar sem salvar o JSON?"):
            return
        self.destroy()

    def _pode_substituir(self) -> bool:
        return not self.alteracoes_pendentes or messagebox.askyesno(
            "Alterações não salvas", "Há alterações na lista. Substituir sem salvar o JSON?"
        )

    def _abrir(self, caminho: Path) -> None:
        try:
            produtos = carregar_produtos(caminho)
            self._definir_produtos(produtos)
            self.caminho_dados = caminho
            self.status.set(f"Arquivo aberto: {caminho.name}")
        except (OSError, ValueError, KeyError, TypeError) as erro:
            messagebox.showerror("Erro ao abrir JSON", str(erro))

    def _abrir_json(self) -> None:
        if not self._pode_substituir():
            return
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos JSON", "*.json")])
        if caminho:
            self._abrir(Path(caminho))

    def _importar_csv(self) -> None:
        if not self._pode_substituir():
            return
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if not caminho:
            return
        try:
            self._definir_produtos(importar_csv(caminho))
            self.alteracoes_pendentes = True
            self.status.set("CSV importado. Use Salvar JSON para guardar a lista.")
        except (OSError, ValueError, KeyError, TypeError) as erro:
            messagebox.showerror("Erro ao importar CSV", str(erro))

    def _definir_produtos(self, produtos: list[Produto]) -> None:
        skus = [p.sku for p in produtos]
        if len(set(skus)) != len(skus):
            raise ValueError("Há SKUs repetidos no arquivo.")
        self.produtos = produtos
        self.selecionado = None
        self.alteracoes_pendentes = False
        self._atualizar_lista()
        self._limpar_campos()

    def _atualizar_lista(self) -> None:
        atual = self.selecionado
        self.lista.delete(*self.lista.get_children())
        ordem = {"Comprar agora": 0, "Comprar em breve": 1, "OK": 2}
        for produto in sorted(self.produtos, key=lambda p: (ordem[situacao(p)], p.nome.lower())):
            estado = situacao(produto)
            if self.filtro.get() != "Todos" and estado != self.filtro.get():
                continue
            termo = self.busca.get().casefold().strip()
            if termo and termo not in (produto.sku + " " + produto.nome).casefold():
                continue
            a = analisar_produto(produto)
            tag = "agora" if estado == "Comprar agora" else "breve" if estado == "Comprar em breve" else ""
            self.lista.insert("", "end", iid=produto.sku, values=(estado, produto.sku, produto.nome,
                              a.estoque_disponivel, a.ponto_reposicao, a.quantidade_sugerida), tags=(tag,))
        if atual and self.lista.exists(atual):
            self.lista.selection_set(atual)

    def _selecionar(self, _evento: object = None) -> None:
        selecao = self.lista.selection()
        if not selecao:
            return
        self.selecionado = selecao[0]
        p = next(p for p in self.produtos if p.sku == self.selecionado)
        valores = {
            "sku": p.sku, "nome": p.nome, "estoque_atual": p.estoque_atual,
            "estoque_a_receber": p.estoque_a_receber, "estoque_reservado": p.estoque_reservado,
            "consumo_medio_diario": p.consumo_medio_diario, "estoque_seguranca": p.estoque_seguranca,
            "prazo_entrega_dias": p.fornecedor.prazo_entrega_dias,
            "periodo_revisao_dias": p.periodo_revisao_dias,
            "compra_minima": p.fornecedor.compra_minima, "multiplo_compra": p.fornecedor.multiplo_compra,
        }
        for chave, valor in valores.items():
            self.campos[chave].set(str(valor))
        self.resumo.set(explicar(p))

    def _limpar_campos(self) -> None:
        for chave, var in self.campos.items():
            var.set("1" if chave in {"compra_minima", "multiplo_compra"} else "0" if chave not in {"sku", "nome"} else "")
        self.resumo.set("Preencha os dados e clique em Salvar produto.")

    def _novo(self) -> None:
        self.lista.selection_remove(self.lista.selection())
        self.selecionado = None
        self._limpar_campos()

    def _salvar_produto(self) -> None:
        try:
            produto = criar_produto_dos_campos({chave: var.get() for chave, var in self.campos.items()})
            # Um fornecedor por SKU evita que editar seu prazo altere outros produtos.
            produto = replace(produto, fornecedor=replace(produto.fornecedor, id=f"FOR-{produto.sku}"))
            if any(p.sku == produto.sku and p.sku != self.selecionado for p in self.produtos):
                raise ValueError("Esse SKU já está cadastrado.")
            if self.selecionado:
                self.produtos = [produto if p.sku == self.selecionado else p for p in self.produtos]
            else:
                self.produtos.append(produto)
            self.selecionado = produto.sku
            self.alteracoes_pendentes = True
            self._atualizar_lista()
            if self.lista.exists(produto.sku):
                self.lista.selection_set(produto.sku)
            self.resumo.set(explicar(produto))
            self.status.set("Produto atualizado na lista. Clique em Salvar JSON para guardar.")
        except (ValueError, OverflowError) as erro:
            messagebox.showerror("Dados inválidos", str(erro))

    def _salvar_json(self) -> None:
        caminho = filedialog.asksaveasfilename(defaultextension=".json", initialfile=self.caminho_dados.name,
                                               filetypes=[("Arquivos JSON", "*.json")])
        if not caminho:
            return
        try:
            salvar_json(caminho, self.produtos)
            self.caminho_dados = Path(caminho)
            self.alteracoes_pendentes = False
            self.status.set(f"Lista salva em {self.caminho_dados.name}.")
        except OSError as erro:
            messagebox.showerror("Erro ao salvar JSON", str(erro))

    def _exportar_csv(self) -> None:
        caminho = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="produtos.csv",
                                               filetypes=[("Arquivos CSV", "*.csv")])
        if caminho:
            try:
                exportar_csv(caminho, self.produtos)
                self.status.set("CSV exportado.")
            except OSError as erro:
                messagebox.showerror("Erro ao exportar CSV", str(erro))

    def _enviar_compra(self) -> None:
        if not self.selecionado:
            messagebox.showinfo("Selecione um produto", "Selecione um produto na lista.")
            return
        produto = next(p for p in self.produtos if p.sku == self.selecionado)
        try:
            pedido_id, quantidade = compra_aprovada(self.caminho_dados.parent / "decisoes.csv", produto.sku)
        except (OSError, ValueError, KeyError) as erro:
            messagebox.showerror("Compra não aprovada", str(erro))
            return
        preco = simpledialog.askstring("Preço da compra", "Preço por unidade (R$):", parent=self)
        if preco is None:
            return
        vencimento = simpledialog.askstring("Vencimento", "Data para pagar (AAAA-MM-DD):", parent=self)
        if vencimento is None:
            return
        try:
            resposta = enviar_compra(produto, pedido_id, quantidade, preco, vencimento.strip())
            verbo = "criada" if resposta.get("criada") else "já existente"
            self.status.set(f"Conta {verbo}: pedido {pedido_id}, valor R$ {resposta['valor']}.")
            messagebox.showinfo("Ponte concluída", "Compra enviada. Em Contas a Pagar, clique em Atualizar.")
        except (ValueError, ConnectionError, KeyError) as erro:
            messagebox.showerror("Não foi possível enviar", str(erro))

    def _decidir(self, decisao: str) -> None:
        if not self.selecionado:
            messagebox.showinfo("Selecione um produto", "Selecione um produto na lista.")
            return
        produto = next(p for p in self.produtos if p.sku == self.selecionado)
        sugerida = analisar_produto(produto).quantidade_sugerida
        quantidade = 0 if decisao == "Adiar" else sugerida
        if decisao == "Ajustar":
            quantidade = simpledialog.askinteger("Ajustar compra", "Nova quantidade:", initialvalue=sugerida,
                                                 minvalue=0, parent=self)
            if quantidade is None:
                return
        motivo = ""
        if decisao in {"Ajustar", "Adiar"}:
            motivo = simpledialog.askstring("Motivo", "Motivo da decisão:", parent=self)
            if motivo is None:
                return
        caminho = self.caminho_dados.parent / "decisoes.csv"
        try:
            registrar_decisao(caminho, produto.sku, decisao, quantidade, motivo)
            self.status.set(f"Decisão registrada em {caminho.name}: {decisao}, {quantidade} unidade(s).")
            if decisao in {"Aceitar", "Ajustar"} and quantidade > 0:
                if messagebox.askyesno("Criar conta a pagar", "Enviar esta compra para Contas a Pagar agora?"):
                    self._enviar_compra()
        except (OSError, ValueError) as erro:
            messagebox.showerror("Erro ao registrar decisão", str(erro))


def iniciar_interface(caminho_dados: Path) -> None:
    Painel(caminho_dados).mainloop()
