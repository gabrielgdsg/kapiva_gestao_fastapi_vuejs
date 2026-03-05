-- Performance Optimization Indexes for LevantamentosTest2
-- These indexes speed up the levantamentos query
-- Apply these to your PostgreSQL database (optional but recommended)

-- 1. Index on PRODUTO table for marca and empresa lookups
-- Speeds up: WHERE pro.cod_marca = ? AND pro.cod_empresa = '1'
CREATE INDEX IF NOT EXISTS idx_produto_marca_empresa 
ON PRODUTO(cod_marca, cod_empresa, flg_mestre);

-- 2. Index on produto_ficha_estoq for movement joins
-- Speeds up: LEFT OUTER JOIN produto_ficha_estoq pfe on (pfe.cod_produto = pro.cod_produto)
CREATE INDEX IF NOT EXISTS idx_produto_ficha_estoq_produto 
ON produto_ficha_estoq(cod_produto, data, cod_origem_movto);

-- 3. Index on nfcompraitem for purchase item joins
-- Speeds up: LEFT OUTER JOIN nfcompraitem it on (pro.cod_empresa = it.cod_empresa and pro.cod_produto = it.cod_produto)
CREATE INDEX IF NOT EXISTS idx_nfcompraitem_produto 
ON nfcompraitem(cod_produto, cod_empresa, cod_interno);

-- 4. Index on nfcompra for purchase filtering
-- Speeds up: WHERE (cb.flg_estorno is null or cb.flg_estorno = 'N')
CREATE INDEX IF NOT EXISTS idx_nfcompra_estorno 
ON nfcompra(cod_empresa, cod_interno, cod_fornece, flg_estorno);

-- 5. Index on PRODUTO for date range queries (if dates are used in future)
CREATE INDEX IF NOT EXISTS idx_produto_datas 
ON PRODUTO(dat_cadastro, dat_ultcompra);

-- Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('produto', 'produto_ficha_estoq', 'nfcompraitem', 'nfcompra')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
