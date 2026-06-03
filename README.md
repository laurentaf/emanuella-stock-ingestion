# emanuella-stock-ingestion

Rotina de ingestão para **forecasts de estoque semanal** — Lojas Emanuella.

Pipeline ETL em 3 estágios que consome dados da API DataMission, transforma e prepara artefatos para dbt.

## Arquitetura

```
API DataMission
      │
      ▼
┌─────────────────┐
│ Estágio 1       │  fetch_inventory_data()
│ Ingestão via API│  → data/inventory_staging.json (JSON bruto)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Estágio 2       │  transform_inventory()
│ Transformação   │  Lê do JSON em disco, seleciona colunas chave
│                 │  → data/inventory_staging.csv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Estágio 3       │  generate_metadata()
│ Artefatos dbt   │  → data/inventory_metadata.json
│                 │  → sql/staging_inventory.sql
└─────────────────┘
```

## Pré-requisitos

- Python 3.10+
- pip

## Setup

```bash
# 1. Clonar o repositório
git clone https://github.com/laurentaf/emanuella-stock-ingestion.git
cd emanuella-stock-ingestion

# 2. Criar ambiente virtual
python -m venv .venv

# 3. Ativar o ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt
```

## Configuração da API

O script usa um token de curta duração fornecido pela plataforma DataMission.
Para sobrescrever o token padrão, defina a variável de ambiente:

```bash
# Windows PowerShell:
$env:API_TOKEN = "seu-token-aqui"

# Linux/Mac:
export API_TOKEN="seu-token-aqui"
```

## Execução

```bash
python scripts/ingestion.py
```

O pipeline executa os 3 estágios em sequência e produz:

| Estágio | Arquivo de saída | Descrição |
|---------|------------------|-----------|
| 1 | `data/inventory_staging.json` | JSON bruto com todos os registros da API |
| 2 | `data/inventory_staging.csv` | CSV transformado com colunas selecionadas |
| 3 | `data/inventory_metadata.json` | Schema simples (coluna/nome/tipo) |
| 3 | `sql/staging_inventory.sql` | Modelo dbt comentado para staging |

## Dados

A API retorna 1000 registros com as seguintes colunas:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `order_id` | string | Identificador único do pedido (UUID) |
| `timestamp` | datetime | Data/hora ISO do pedido |
| `customer_id` | integer | Identificador do cliente |
| `product_category` | string | Categoria do produto |
| `price` | float | Preço unitário em reais |
| `quantity` | integer | Quantidade de unidades |
| `store_location` | string | Nome da loja |

## Regras de qualidade

Ver [data/quality_rules.md](data/quality_rules.md) para as regras de qualidade
documentadas aplicadas aos dados.

## Decisões técnicas

Ver [decisions/](decisions/) para Architecture Decision Records.

## Agendamento (trigger/SLA)

O pipeline é executado manualmente ou pode ser agendado via cron/CI.
Ver [.github/workflows/ingest.yml](.github/workflows/ingest.yml).

**Trigger sugerido:** diário às 06:00 UTC
**SLA sugerido:** pipeline completo em < 5 minutos (para 1000 registros)

## Projeto

Este é um projeto público gerado pela [LAOS](https://github.com/laurentaf/laos) —
Laurent Agent Operating System.
