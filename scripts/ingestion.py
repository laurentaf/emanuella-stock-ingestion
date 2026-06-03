"""
Script de ingestão de dados de inventário — Lojas Emanuella.

Estágio 1: Estruturar ingestão inicial
- fetch_inventory_data(): consome a API da DataMission
- Persiste o JSON bruto em data/inventory_staging.json

Estágio 2: Transformar e salvar dados
- transform_inventory(): carrega o JSON do disco, loga linhas, seleciona colunas
- Salva resultado em data/inventory_staging.csv

Estágio 3: Preparar artefatos para dbt
- Gera data/inventory_metadata.json com schema simples (coluna/nome/tipo)
- sql/staging_inventory.sql com modelo dbt comentado
"""

import requests
import pandas as pd
import json
import os
import sys
from datetime import datetime

# Carrega variáveis do .env se existir (para desenvolvimento local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configurações
PROJECT_ID = "1751329c-152c-42dd-822d-ad62f1328c01"

# O token da API deve vir da variável de ambiente ou do arquivo .env.
# Para configurar, copie .env.example para .env e preencha o token:
#   copy .env.example .env   (Windows)
#   cp .env.example .env      (Linux/Mac)
API_TOKEN = os.environ.get("API_TOKEN")
if not API_TOKEN:
    print("=" * 60)
    print("  ERRO: Variavel de ambiente API_TOKEN nao definida.")
    print("  Copie .env.example para .env e configure o token, ou")
    print("  execute com: set API_TOKEN=seu-token (Windows)")
    print("  execute com: export API_TOKEN=seu-token (Linux/Mac)")
    print("=" * 60)
    sys.exit(1)

BASE_URL = "https://api.datamission.com.br/projects"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


# =============================================================================
# Estágio 1: Ingestão via API
# =============================================================================

def fetch_inventory_data() -> list[dict]:
    """
    Consome a API de datasets da DataMission e retorna a lista de registros.

    Endpoint:
        GET https://api.datamission.com.br/projects/{project_id}/dataset?format=json

    Returns:
        list[dict]: Lista de dicionários com os dados de inventário.

    Raises:
        requests.exceptions.RequestException: Se a requisição falhar.
    """
    url = f"{BASE_URL}/{PROJECT_ID}/dataset?format=json"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    print(f"[fetch_inventory_data] Chamando API: {url}")
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    print(f"[fetch_inventory_data] {len(data)} registros obtidos com sucesso.")
    return data


def save_raw_json(data: list[dict], filepath: str) -> str:
    """
    Persiste os dados brutos em um arquivo JSON no disco.

    Args:
        data: Lista de dicionários com os dados.
        filepath: Caminho do arquivo JSON de saída.

    Returns:
        str: Caminho do arquivo salvo.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[save_raw_json] JSON bruto salvo em: {filepath} ({len(data)} registros)")
    return filepath


# =============================================================================
# Estágio 2: Transformação a partir do JSON persistido
# =============================================================================

def transform_inventory(json_path: str) -> pd.DataFrame:
    """
    Carrega o JSON persistido do disco, loga quantas linhas foram carregadas
    e seleciona as colunas para análise de forecast de estoque.

    Colunas de saída (7 colunas = todas as colunas da API):
        - order_id: identificador único do pedido
        - timestamp: data/hora do pedido (para séries temporais)
        - customer_id: identificador do cliente
        - product_category: categoria do produto (dimensão de análise)
        - price: preço unitário
        - quantity: quantidade (métrica principal para forecast)
        - store_location: loja (dimensão geográfica)

    Args:
        json_path: Caminho do arquivo JSON gerado no Estágio 1.

    Returns:
        pd.DataFrame: DataFrame com todas as colunas transformadas.
    """
    KEY_COLUMNS = [
        "order_id",
        "timestamp",
        "customer_id",
        "product_category",
        "price",
        "quantity",
        "store_location",
    ]

    print(f"[transform_inventory] Carregando JSON do disco: {json_path}")

    # Abre o JSON persistido no estágio 1
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows_loaded = len(data)
    print(f"[transform_inventory] Linhas carregadas do JSON: {rows_loaded}")

    df = pd.DataFrame(data)

    # Seleciona apenas as colunas chave
    df_transformed = df[KEY_COLUMNS].copy()

    # Converte timestamp para datetime
    df_transformed["timestamp"] = pd.to_datetime(df_transformed["timestamp"])

    print(f"[transform_inventory] Colunas selecionadas: {list(df_transformed.columns)}")
    print(f"[transform_inventory] Linhas após transformacao: {len(df_transformed)}")

    return df_transformed


def save_staging_csv(df: pd.DataFrame, filepath: str) -> None:
    """
    Salva o DataFrame transformado em formato CSV.

    Args:
        df: DataFrame com os dados transformados.
        filepath: Caminho do arquivo CSV de saída.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8")
    print(f"[save_staging_csv] CSV salvo em: {filepath} ({len(df)} linhas)")


# =============================================================================
# Estágio 3: Artefatos para dbt
# =============================================================================

def generate_metadata_from_df(df: pd.DataFrame) -> list[dict]:
    """
    Gera o schema simples a partir de um DataFrame ja transformado,
    garantindo que o metadata reflita EXATAMENTE as colunas do CSV final.

    Schema: coluna/nome/tipo — formato simples para consumo pelo dbt.

    Args:
        df: DataFrame apos transformacao (mesmo que vai para o CSV).

    Returns:
        list[dict]: Schema simplificado das colunas.
    """
    COLUMN_NAMES = {
        "order_id": "ID do Pedido",
        "timestamp": "Data do Pedido",
        "customer_id": "ID do Cliente",
        "product_category": "Categoria do Produto",
        "price": "Preco Unitario",
        "quantity": "Quantidade",
        "store_location": "Loja",
    }

    metadata = []
    for col in df.columns:
        col_type = df[col].dtype

        if pd.api.types.is_integer_dtype(col_type):
            type_name = "integer"
        elif pd.api.types.is_float_dtype(col_type):
            type_name = "float"
        elif pd.api.types.is_datetime64_any_dtype(col_type):
            type_name = "datetime"
        else:
            type_name = "string"

        metadata.append({
            "column_name": col,
            "name": COLUMN_NAMES.get(col, col.replace("_", " ").title()),
            "type": type_name,
        })

    return metadata


def save_metadata(metadata: list[dict], filepath: str, total_records: int) -> None:
    """
    Salva o schema dos dados em um arquivo JSON.
    Chamada APOS salvar o CSV, como parte do pipeline.

    Args:
        metadata: Lista com schema das colunas.
        filepath: Caminho do arquivo JSON de saida.
        total_records: Numero total de registros processados.
    """
    payload = {
        "project_id": PROJECT_ID,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_records": total_records,
        "columns": metadata,
    }
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[save_metadata] Metadados salvos em: {filepath}")


# =============================================================================
# Pipeline principal
# =============================================================================

def main():
    """
    Pipeline principal em 3 estagios:

    Estagio 1: Busca dados da API e persiste JSON bruto no disco
    Estagio 2: Le JSON do disco, transforma, salva CSV
    Estagio 3: Gera metadados e artefatos para dbt
    """
    print("=" * 60)
    print("  Lojas Emanuella — Ingestao de Inventario (3 estagios)")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Estagio 1: Ingestao via API + persistencia do JSON bruto
    # ------------------------------------------------------------------
    print("\n--- Estagio 1: Ingestao via API ---")
    raw_data = fetch_inventory_data()

    json_path = os.path.join(DATA_DIR, "inventory_staging.json")
    save_raw_json(raw_data, json_path)

    # ------------------------------------------------------------------
    # Estagio 2: Carregar JSON do disco, transformar, salvar CSV
    # ------------------------------------------------------------------
    print("\n--- Estagio 2: Transformacao (a partir do JSON em disco) ---")
    df_transformed = transform_inventory(json_path)

    csv_path = os.path.join(DATA_DIR, "inventory_staging.csv")
    save_staging_csv(df_transformed, csv_path)

    # ------------------------------------------------------------------
    # Estagio 3: Gerar metadados APOS salvar o CSV
    # ------------------------------------------------------------------
    print("\n--- Estagio 3: Artefatos para dbt ---")
    # Metadata gerado a partir do DataFrame TRANSFORMADO (df_transformed)
    # para garantir consistencia com as colunas do CSV final
    metadata = generate_metadata_from_df(df_transformed)
    metadata_path = os.path.join(DATA_DIR, "inventory_metadata.json")
    save_metadata(metadata, metadata_path, len(df_transformed))

    print("\n[OK] Pipeline completo (3 estagios)!")
    print(f"   JSON bruto:    {json_path}")
    print(f"   CSV staging:   {csv_path}")
    print(f"   Metadados:     {metadata_path}")
    print(f"   SQL dbt:       sql/staging_inventory.sql")


if __name__ == "__main__":
    main()
