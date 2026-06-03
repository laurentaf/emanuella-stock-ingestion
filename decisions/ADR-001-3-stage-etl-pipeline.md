# ADR-001: Pipeline ETL em 3 estágios

## Status

Aceito

## Contexto

Precisamos de um pipeline de ingestão de dados de inventário para a Lojas Emanuella
que seja:
- Desacoplado (cada estágio pode rodar independentemente)
- Rastreável (dados intermediários persistem no disco)
- Preparado para dbt downstream

A fonte é uma API REST (`/dataset?format=json`) que retorna 1000 registros
com 7 colunas (order_id, timestamp, customer_id, product_category, price,
quantity, store_location).

## Decisão

Adotar uma arquitetura de pipeline em 3 estágios com artefatos intermediários
persistidos em disco:

1. **Estágio 1 — Ingestão**: `fetch_inventory_data()` chama a API e persiste
   o JSON bruto em `data/inventory_staging.json`. Isso garante que os dados
   originais estejam disponíveis para reprocessamento sem chamar a API novamente.

2. **Estágio 2 — Transformação**: `transform_inventory()` lê o JSON do disco
   (desacoplado da API), seleciona as 5 colunas chave para forecast de estoque
   (timestamp, product_category, price, quantity, store_location), e salva em
   `data/inventory_staging.csv`.

3. **Estágio 3 — Artefatos dbt**: Gera `data/inventory_metadata.json` com
   schema simples (coluna/nome/tipo) e mantém `sql/staging_inventory.sql`
   como modelo dbt de staging.

## Consequências

**Positivas:**
- Estágio 2 não depende da API (pode rodar offline com o JSON em disco)
- Dados brutos preservados para reprodutibilidade
- Pipeline pode ser retomado de qualquer estágio
- Preparado para integração com dbt (modelo staging + metadados)

**Negativas:**
- Duplicação de armazenamento (JSON bruto + CSV transformado)
- Pipeline sequencial (estágios não paralelizáveis)
- Snapshots não versionados por data (identificados apenas pelo conteúdo do metadata)

## Alternativas consideradas

- **Pipeline inline**: Tudo em memória, sem artefatos intermediários.
  Rejeitado por falta de rastreabilidade e impossibilidade de reprocessamento.
- **ETL em banco**: Carregar direto no warehouse. Rejeitado por não atender
  ao requisito de ter artefatos versionados no repositório.
