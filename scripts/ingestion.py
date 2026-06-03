"""
Script de ingestão de dados de inventário — Lojas Emanuella.

Estágio 1: Estruturar ingestão inicial
- fetch_inventory_data(): consome a API da DataMission e retorna os dados
- Gera data/inventory_staging.csv com os dados brutos
- Gera data/inventory_metadata.json com schema das colunas

Estágio 2: Transformar e salvar dados
- transform_inventory(): carrega JSON, seleciona colunas chave, salva CSV
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

# Configurações
PROJECT_ID = "1751329c-152c-42dd-822d-ad62f1328c01"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsYXVyZW50YWxwIiwidHlwZSI6ImFwaV9rZXkiLCJleHAiOjE3ODMwNTI1NDd9.ab-LzICwxn5hR-XhyLVjBBKMzECpKPLWIGKbSmCXXJc"
BASE_URL = "https://api.datamission.com.br/projects"
# Caminhos relativos ao diretório raiz do projeto
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


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


def save_staging_csv(data: list[dict], filepath: str) -> None:
    """
    Salva os dados brutos em formato CSV.

    Args:
        data: Lista de dicionários com os dados.
        filepath: Caminho do arquivo CSV de saída.
    """
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8")
    print(f"[save_staging_csv] CSV salvo em: {filepath} ({len(df)} linhas)")


def generate_metadata(data: list[dict]) -> list[dict]:
    """
    Gera o schema dos dados no formato:
    [
        {
            "column_name": "nome_da_coluna",
            "type": "tipo_python/tipo_banco",
            "description": "Descrição da coluna",
            "nullable": true/false,
            "sample_values": ["valor1", "valor2", ...]
        },
        ...
    ]

    Args:
        data: Lista de dicionários com os dados.

    Returns:
        list[dict]: Schema das colunas.
    """
    if not data:
        return []

    df = pd.DataFrame(data)
    metadata = []

    for col in df.columns:
        col_type = df[col].dtype
        null_count = int(df[col].isna().sum())
        sample_vals = df[col].dropna().unique()[:3].tolist()
        sample_vals = [str(v) for v in sample_vals]

        # Mapeia dtype pandas para tipo legível
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
            "type": type_name,
            "description": "",  # Preenchido manualmente ou em estágio futuro
            "nullable": null_count > 0,
            "sample_values": sample_vals,
        })

    return metadata


def save_metadata(metadata: list[dict], filepath: str, total_records: int) -> None:
    """
    Salva o schema dos dados em um arquivo JSON.

    Args:
        metadata: Lista com schema das colunas.
        filepath: Caminho do arquivo JSON de saída.
        total_records: Número total de registros processados.
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


def transform_inventory(data: list[dict]) -> pd.DataFrame:
    """
    Transforma os dados brutos da API selecionando as colunas chave
    para análise de forecast de estoque.

    Colunas selecionadas:
        - timestamp: data/hora do pedido (para séries temporais)
        - product_category: categoria do produto (dimensão de análise)
        - price: preço unitário
        - quantity: quantidade (métrica principal para forecast)
        - store_location: loja (dimensão geográfica)

    Args:
        data: Lista de dicionários com os dados brutos da API.

    Returns:
        pd.DataFrame: DataFrame com as colunas transformadas.
    """
    KEY_COLUMNS = [
        "timestamp",
        "product_category",
        "price",
        "quantity",
        "store_location",
    ]

    df = pd.DataFrame(data)
    rows_before = len(df)

    # Seleciona apenas as colunas chave
    df_transformed = df[KEY_COLUMNS].copy()

    # Converte timestamp para datetime
    df_transformed["timestamp"] = pd.to_datetime(df_transformed["timestamp"])

    rows_after = len(df_transformed)
    print(f"[transform_inventory] Linhas carregadas: {rows_after}")
    print(f"[transform_inventory] Colunas selecionadas: {list(df_transformed.columns)}")

    return df_transformed


def main():
    """
    Pipeline principal:
    Estágio 1: Ingestão bruta via API
    Estágio 2: Transformação e seleção de colunas chave
    """
    print("=" * 60)
    print("  Lojas Emanuella — Ingestão de Inventário")
    print("=" * 60)

    # --- Estágio 1: Fetch dados brutos da API ---
    print("\n--- Estágio 1: Ingestão ---")
    raw_data = fetch_inventory_data()

    # --- Estágio 2: Transformar dados ---
    print("\n--- Estágio 2: Transformação ---")
    df_transformed = transform_inventory(raw_data)

    # Salvar CSV transformado como staging
    csv_path = os.path.join(DATA_DIR, "inventory_staging.csv")
    save_staging_csv(df_transformed.to_dict(orient="records"), csv_path)

    # Gerar e salvar metadados do schema
    metadata = generate_metadata(raw_data)
    metadata_path = os.path.join(DATA_DIR, "inventory_metadata.json")
    save_metadata(metadata, metadata_path, len(raw_data))

    print("\n[OK] Estagio 2 concluido com sucesso!")
    print(f"   CSV transformado: {csv_path}")
    print(f"   Metadados: {metadata_path}")


if __name__ == "__main__":
    main()
