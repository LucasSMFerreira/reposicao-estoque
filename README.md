# Reposição Automática de Estoque 

![Tela inicial da Reposição com dados fictícios](docs/screenshots/tela-inicial.png)

Aplicação Python leve para acompanhar produtos e sugerir compras. Usa apenas a biblioteca padrão, incluindo Tkinter para a janela. Nenhum pedido é enviado automaticamente.

## Abrir

Requer Python 3.10 ou superior. Na pasta do projeto:

```bash
python main.py
```

A lista mostra primeiro **Comprar agora**, depois **Comprar em breve** e **OK**. Use a busca ou o filtro para achar produtos. Clique em uma linha para ver o motivo da sugestão. **Comprar em breve** é um aviso: o estoque está acima do ponto de reposição, mas pode chegar a ele antes da próxima revisão. A quantidade sugerida pode ser zero até o ponto ser atingido.

## Usar os dados

- **Novo produto** limpa o formulário. Preencha os campos e clique em **Salvar produto**.
- Para editar, selecione uma linha, altere os campos e clique em **Salvar produto**.
- **Salvar JSON** guarda a lista em um arquivo escolhido por você. Até clicar nele, mudanças no formulário não são gravadas no arquivo.
- **Abrir JSON** carrega uma lista salva. **Importar CSV** substitui a lista atual por um CSV no formato exportado pelo programa. **Exportar CSV** cria um arquivo que pode ser aberto em planilhas.
- **Aceitar sugestão**, **Ajustar** e **Adiar** registram a decisão em `decisoes.csv`, na mesma pasta do JSON aberto ou salvo. Isso não altera o estoque nem envia pedidos.

O arquivo `data/produtos.json` contém exemplos fictícios. Para trabalhar com dados reais, salve uma cópia em outro local.

## Entenda os campos

- **Estoque disponível** = atual + a receber − reservado.
- **Consumo médio/dia** = vendas médias de uma unidade por dia.
- **Estoque de segurança** = reserva para imprevistos.
- **Prazo de entrega** = dias entre comprar e receber.
- **Revisão** = dias até a próxima conferência do estoque.
- **Compra mínima** e **múltiplo** = limites do fornecedor para o tamanho do pedido.

Ponto de reposição = consumo médio/dia × prazo de entrega + estoque de segurança. Quando o disponível chega ao ponto, a sugestão cobre o prazo de entrega e o período de revisão, respeitando a compra mínima e o múltiplo.

## Terminal e testes

```bash
python main.py --cli
python main.py --cli --dados caminho/para/produtos.json
python -m unittest discover -s tests -v
```

## Estrutura

```text
main.py                 Entrada da janela e do terminal
src/database/           Leitura, gravação, CSV e decisões
src/estoque/            Produto e estoque disponível
src/reposicao/          Cálculos de reposição
src/fornecedores/       Fornecedor
src/interface/          Janela Tkinter
data/                   Exemplos fictícios
tests/                  Testes
```

A lógica permanece separada da interface para facilitar o futuro executável e a integração com previsão de demanda.

## Enviar uma compra aprovada para Contas a Pagar

Abra o projeto de [Contas a Pagar](https://github.com/LucasSMFerreira/Controle-Contas) em outra janela, salve o arquivo de contas e clique em **Ativar ponte**. Em Reposição, selecione um produto e clique em **Aceitar sugestão** ou **Ajustar**. O programa oferece criar a conta a pagar; informe preço por unidade e vencimento. Se a API estiver desligada, a decisão fica registrada e o botão **Enviar para Contas a Pagar** permite tentar novamente. A mesma aprovação tem um número de pedido estável para evitar contas duplicadas.

O programa não compra mercadorias nem efetua pagamentos. O envio acontece apenas depois de uma decisão de compra aprovada.

## Como os projetos se encaixam

Este painel funciona sozinho: calcula a necessidade de reposição e registra decisões sem depender dos outros projetos. Quando o usuário aprova uma compra e ativa a API local de Contas a Pagar, o botão de envio cria a despesa correspondente com número de pedido, valor e vencimento. O [projeto de Previsão de Demanda](https://github.com/LucasSMFerreira/Previsao-demanda-estoque) pode futuramente fornecer a estimativa de consumo; essa etapa ainda não está conectada automaticamente.

Os três módulos foram mantidos em repositórios separados para compor uma aplicação final sem concentrar toda a lógica em um único arquivo.
