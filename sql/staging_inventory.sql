-- ============================================================================
-- staging_inventory.sql
-- Definição da tabela de staging para dados brutos de inventário
-- Lojas Emanuella — Pipeline de Forecast de Estoque Semanal
--
-- Fonte: API DataMission (endpoint /dataset)
-- Tabela: staging.inventory
-- Descrição: Dados brutos de pedidos/inventário coletados via API.
--            Usada como entrada para transformações e modelos dbt.
-- ============================================================================

-- Criação do schema de staging (executar uma vez)
-- CREATE SCHEMA IF NOT EXISTS staging;

-- Tabela staging para dados de inventário
CREATE TABLE IF NOT EXISTS staging.inventory (
    -- Identificador único do pedido (UUID v4)
    -- Ex: "ed5e39f2-485c-45b2-b090-4e05f24ada76"
    order_id            TEXT        NOT NULL,

    -- Timestamp ISO do pedido
    -- Formato: "YYYY-MM-DDTHH:MM:SS.ffffff"
    -- Ex: "2026-06-01T01:36:09.833521"
    timestamp           TIMESTAMP   NOT NULL,

    -- Identificador do cliente (inteiro)
    -- Ex: 8333
    customer_id         BIGINT      NOT NULL,

    -- Categoria do produto
    -- Ex: "Moda", "Eletrônicos", "Alimentos", etc.
    product_category    TEXT        NOT NULL,

    -- Preço unitário do produto (em reais)
    -- Ex: 89.77
    price               DECIMAL(10,2) NOT NULL,

    -- Quantidade de unidades no pedido
    -- Ex: 5
    quantity            INTEGER     NOT NULL,

    -- Localização/loja onde o pedido foi feito
    -- Ex: "da Costa da Praia"
    store_location      TEXT        NOT NULL,

    -- Metadados de ingestão
    ingested_at         TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- Comentários das colunas (para documentação no banco)
COMMENT ON TABLE staging.inventory IS
    'Dados brutos de pedidos/inventário para forecast de estoque semanal. Fonte: API DataMission.';

COMMENT ON COLUMN staging.inventory.order_id IS
    'Identificador único do pedido (UUID v4). Chave primária natural.';

COMMENT ON COLUMN staging.inventory.timestamp IS
    'Data e hora ISO do pedido. Usado para janelas temporais e forecasts.';

COMMENT ON COLUMN staging.inventory.customer_id IS
    'Identificador do cliente. Pode ser usado para agregações por cliente.';

COMMENT ON COLUMN staging.inventory.product_category IS
    'Categoria do produto (ex: Moda, Eletrônicos, Alimentos). Dimensão de análise.';

COMMENT ON COLUMN staging.inventory.price IS
    'Preço unitário do produto em reais (BRL).';

COMMENT ON COLUMN staging.inventory.quantity IS
    'Quantidade de unidades vendidas no pedido.';

COMMENT ON COLUMN staging.inventory.store_location IS
    'Nome da loja/localização onde o pedido foi realizado.';

COMMENT ON COLUMN staging.inventory.ingested_at IS
    'Timestamp de quando o registro foi ingerido no banco. Preenchido automaticamente.';
