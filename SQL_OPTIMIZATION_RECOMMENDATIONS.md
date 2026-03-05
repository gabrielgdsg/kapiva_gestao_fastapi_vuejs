# SQL Query Optimization Recommendations

## Current Query Analysis

The `load_estoque_from_db` query performs multiple LEFT OUTER JOINs and aggregations which can be slow for large datasets.

## Critical Performance Issues

### 1. Missing WHERE Clause on Date Range
The current query checks `dat_cadastro_ini` and `dat_cadastro_fim` for NULL but doesn't actually filter by these dates:

```sql
where pro.cod_empresa = '1'
      and %s is not null
      and %s is not null
```

**Problem:** This loads ALL products regardless of date range!

**Fix:** Add actual date filtering:

```sql
where pro.cod_empresa = '1'
      and pro.dat_cadastro >= %s
      and pro.dat_cadastro <= %s
      and m.cod_marca = %s
```

### 2. Recommended Indexes

Create these indexes to speed up the query:

```sql
-- Critical indexes for WHERE clause
CREATE INDEX IF NOT EXISTS idx_produto_empresa_marca_cadastro 
    ON PRODUTO(cod_empresa, cod_marca, dat_cadastro);

CREATE INDEX IF NOT EXISTS idx_produto_empresa_cadastro 
    ON PRODUTO(cod_empresa, dat_cadastro);

-- Foreign key indexes for JOIN operations
CREATE INDEX IF NOT EXISTS idx_produto_marca 
    ON PRODUTO(cod_marca);

CREATE INDEX IF NOT EXISTS idx_produto_grade 
    ON PRODUTO(cod_grade);

CREATE INDEX IF NOT EXISTS idx_produto_tamanho 
    ON PRODUTO(cod_grade, cod_tamanho);

CREATE INDEX IF NOT EXISTS idx_produto_cor 
    ON PRODUTO(cod_cor);

CREATE INDEX IF NOT EXISTS idx_produto_grupo_subgrupo 
    ON PRODUTO(cod_grupo, cod_subgrupo);

-- NF Compra indexes
CREATE INDEX IF NOT EXISTS idx_nfcompraitem_empresa_produto 
    ON nfcompraitem(cod_empresa, cod_produto);

CREATE INDEX IF NOT EXISTS idx_nfcompra_empresa_interno 
    ON nfcompra(cod_empresa, cod_interno);

-- Produto ficha estoque index
CREATE INDEX IF NOT EXISTS idx_produto_ficha_estoq_produto 
    ON produto_ficha_estoq(cod_produto);
```

### 3. Query Structure Issues

**Current Issue:** The query uses `GROUP BY` with all columns, which prevents proper aggregation optimization.

**Recommendation:** Consider splitting into two queries:
1. Get base product data (without movimento details)
2. Get movimento data separately and join in application layer

This would allow better caching and pagination.

### 4. Data Volume Concerns

**Current behavior:** Loading ALL movements for ALL products in date range.

**Recommendations:**
- Add LIMIT clause for pagination
- Consider filtering movements by date as well
- Add an option to load movements on-demand (lazy loading)

## Optimized Query Version

```sql
SELECT 
    pro.cod_grupo, gu.des_grupo, 
    pro.cod_subgrupo, su.des_subgrupo,
    pro.cod_produto, pro.des_produto, 
    pro.cod_barra, pro.cod_referencia,
    COALESCE(SUM(it.qtd_produto), 0) as qtd, 
    pro.saldo_estoque,
    pro.vlr_custo_bruto, pro.vlr_custo_aquis, 
    pro.vlr_venda1, 
    COALESCE(SUM(it.vlr_total), 0) as total,
    pro.cod_grade, g.des_grade,
    pro.cod_tamanho, t.des_tamanho,
    pro.cod_cor, c.des_cor,
    pro.dat_cadastro, pro.dat_ultcompra, 
    cb.cod_fornece, 
    f.raz_fornece, f.fan_fornece,
    m.cod_marca, m.nom_marca,
    pfe.tipo_movto, pfe.qtd_movto, 
    pfe.data as data_movto, 
    pfe.cod_movto, pfe.cod_origem_movto
FROM PRODUTO pro
    INNER JOIN MARCA m ON m.COD_MARCA = pro.COD_MARCA
    INNER JOIN grade_tamanho g ON g.cod_grade = pro.cod_grade
    INNER JOIN tamanho t ON t.cod_grade = pro.cod_grade 
        AND t.cod_tamanho = pro.cod_tamanho
    LEFT OUTER JOIN cores c ON c.cod_cor = pro.cod_cor
    LEFT OUTER JOIN grupo_produto gu ON gu.cod_grupo = pro.cod_grupo
    LEFT OUTER JOIN subgrupo_produto su ON su.cod_grupo = pro.cod_grupo 
        AND su.cod_subgrupo = pro.cod_subgrupo
    LEFT OUTER JOIN nfcompraitem it ON pro.cod_empresa = it.cod_empresa 
        AND pro.cod_produto = it.cod_produto
    LEFT OUTER JOIN nfcompra cb ON cb.cod_empresa = it.cod_empresa 
        AND cb.cod_interno = it.cod_interno
        AND (cb.flg_estorno IS NULL OR cb.flg_estorno = 'N')
    LEFT OUTER JOIN fornecedor f ON cb.cod_fornece = f.cod_fornece
    LEFT OUTER JOIN produto_ficha_estoq pfe ON pfe.cod_produto = pro.cod_produto
WHERE pro.cod_empresa = '1'
    AND pro.dat_cadastro >= %s
    AND pro.dat_cadastro <= %s
    AND m.cod_marca = %s
    AND (pro.flg_mestre = 'N' OR pro.flg_mestre IS NULL)
GROUP BY 
    pro.cod_grupo, gu.des_grupo, 
    pro.cod_subgrupo, su.des_subgrupo,
    pro.cod_produto, pro.des_produto, 
    pro.cod_barra, pro.cod_referencia,
    pro.vlr_custo_bruto, pro.vlr_custo_aquis, 
    pro.vlr_venda1,
    pro.cod_grade, g.des_grade, 
    pro.saldo_estoque,
    pro.cod_tamanho, t.des_tamanho,
    pro.cod_cor, c.des_cor,
    pro.dat_cadastro, pro.dat_ultcompra, 
    cb.cod_fornece,
    f.raz_fornece, f.fan_fornece,
    m.cod_marca, m.nom_marca,
    pfe.tipo_movto, pfe.qtd_movto, 
    data_movto, pfe.cod_movto, 
    pfe.cod_origem_movto
ORDER BY pro.dat_ultcompra DESC NULLS LAST, pro.dat_cadastro DESC
```

**Key improvements:**
1. Changed MARCA join from LEFT to INNER (marca is required)
2. Moved estorno check to JOIN condition
3. Used COALESCE for NULL handling
4. Added ORDER BY for most recent items first
5. Used NULLS LAST for proper NULL handling

## Performance Monitoring

Add query execution time logging:

```python
import time

@classmethod
def load_estoque_from_db(cls, dat_cadastro_ini, dat_cadastro_fim, cod_marca):
    start_time = time.time()
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute('''... query ...''', 
                      (dat_cadastro_ini, dat_cadastro_fim, cod_marca))
        dados_estoque = cursor.fetchall()
    execution_time = time.time() - start_time
    print(f"Query execution time: {execution_time:.2f}s - {len(dados_estoque)} rows")
    return dados_estoque
```

## Next Steps

1. Apply the date filtering fix (critical)
2. Create indexes in test environment
3. Test query performance with EXPLAIN ANALYZE
4. Consider implementing pagination
5. Add query result caching
