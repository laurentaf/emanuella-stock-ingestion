# Regras de Qualidade — Dados de Inventário

Regras documentadas para validação dos dados de inventário da Lojas Emanuella.

## Regras aplicadas no pipeline

| ID | Regra | Coluna | Descrição | Severidade |
|----|-------|--------|-----------|------------|
| DQ-01 | NOT NULL | `order_id` | Identificador do pedido não pode ser nulo | blocker |
| DQ-02 | NOT NULL | `timestamp` | Data do pedido não pode ser nula | blocker |
| DQ-03 | NOT NULL | `customer_id` | ID do cliente não pode ser nulo | blocker |
| DQ-04 | NOT NULL | `product_category` | Categoria do produto não pode ser nula | blocker |
| DQ-05 | POSITIVE | `price` | Preço unitário deve ser ≥ 0 | blocker |
| DQ-06 | POSITIVE | `quantity` | Quantidade deve ser ≥ 1 | blocker |
| DQ-07 | NOT NULL | `store_location` | Nome da loja não pode ser nulo | blocker |
| DQ-08 | UNIQUE | `order_id` | ID do pedido deve ser único | blocker |
| DQ-09 | RANGE | `quantity` | Quantidade entre 1 e 1000 | warning |
| DQ-10 | RANGE | `price` | Preço entre 0.01 e 99999.99 | warning |

## Como essas regras são aplicadas

### No banco (via dbt)
```sql
-- DQ-05 e DQ-06: Constraints de integridade
ALTER TABLE staging.inventory ADD CONSTRAINT ck_price_positive CHECK (price >= 0);
ALTER TABLE staging.inventory ADD CONSTRAINT ck_quantity_positive CHECK (quantity >= 1);

-- DQ-08: Garantia de unicidade
ALTER TABLE staging.inventory ADD CONSTRAINT uq_order_id UNIQUE (order_id);
```

### No script Python
O script `ingestion.py` não aplica validações destrutivas (não remove linhas),
mas registra no log a contagem de registros processados. Validações mais
rigorosas devem ser implementadas em modelos dbt downstream.
