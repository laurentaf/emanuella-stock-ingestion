-- ============================================================================
-- staging_inventory.sql
-- Modelo de staging para dbt — Lojas Emanuella
-- Pipeline de Forecast de Estoque Semanal
--
-- Este modelo é consumido pelo dbt como uma staging layer.
-- Ele lê os dados brutos do CSV ingerido via API e os prepara
-- para os modelos downstream (marts de forecast).
--
-- Uso no dbt:
--   {{ config(materialized='table', schema='staging') }}
--
-- Tabela de origem no data warehouse:
--   raw.inventory (ou referência ao CSV via external table)
-- ============================================================================

WITH source AS (
    -- Fonte: data/inventory_staging.csv gerado pelo pipeline de ingestão
    -- API: https://api.datamission.com.br/projects/{project_id}/dataset?format=json
    SELECT
        order_id,
        timestamp,
        customer_id,
        product_category,
        price,
        quantity,
        store_location
    FROM {{ source('raw', 'inventory') }}
),

renamed AS (
    -- Renomeia e tipa as colunas para o padrão analítico
    SELECT
        -- Identificador único do pedido (UUID v4)
        -- Ex: "ed5e39f2-485c-45b2-b090-4e05f24ada76"
        order_id                        AS id_pedido,

        -- Data e hora ISO do pedido
        -- Ex: "2026-06-01T01:36:09.833521"
        CAST(timestamp AS TIMESTAMP)    AS dt_pedido,

        -- Identificador do cliente
        -- Ex: 8333
        customer_id                     AS id_cliente,

        -- Categoria do produto
        -- Ex: "Moda", "Eletrônicos", "Alimentos"
        product_category                AS categoria_produto,

        -- Preço unitário em reais (BRL)
        -- Ex: 89.77
        CAST(price AS DECIMAL(10,2))   AS preco_unitario,

        -- Quantidade de unidades no pedido
        -- Ex: 5
        quantity                        AS quantidade,

        -- Nome da loja onde o pedido foi realizado
        -- Ex: "da Costa da Praia"
        store_location                  AS loja,

        -- Timestamp de ingestão (preenchido pelo pipeline)
        CURRENT_TIMESTAMP               AS ingested_at

    FROM source
)

-- Saída final: tabela staging pronta para consumo dos marts
SELECT * FROM renamed
