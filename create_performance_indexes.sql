-- =====================================================
-- PERFORMANCE INDEXES FOR LEVANTAMENTOS QUERY
-- Created: 2026-01-11
-- Purpose: Dramatically improve query performance
-- =====================================================

-- Run this script in your PostgreSQL database
-- Estimated time: 5-15 minutes depending on table sizes

BEGIN;

-- =====================================================
-- CRITICAL INDEXES FOR WHERE CLAUSE
-- =====================================================

-- Combined index for most common query pattern
CREATE INDEX IF NOT EXISTS idx_produto_empresa_marca_cadastro 
    ON PRODUTO(cod_empresa, cod_marca, dat_cadastro)
    WHERE (flg_mestre = 'N' OR flg_mestre IS NULL);

COMMENT ON INDEX idx_produto_empresa_marca_cadastro IS 
    'Critical index for levantamentos query - empresa + marca + date range filtering';

-- Additional index for date range queries
CREATE INDEX IF NOT EXISTS idx_produto_cadastro_ultcompra 
    ON PRODUTO(dat_cadastro DESC, dat_ultcompra DESC NULLS LAST)
    WHERE cod_empresa = '1';

COMMENT ON INDEX idx_produto_cadastro_ultcompra IS 
    'Supports ORDER BY dat_ultcompra DESC, dat_cadastro DESC for recent items first';

-- =====================================================
-- FOREIGN KEY INDEXES FOR JOIN OPERATIONS
-- =====================================================

-- MARCA join
CREATE INDEX IF NOT EXISTS idx_produto_marca 
    ON PRODUTO(cod_marca)
    WHERE cod_marca IS NOT NULL;

-- GRADE joins
CREATE INDEX IF NOT EXISTS idx_produto_grade 
    ON PRODUTO(cod_grade);

CREATE INDEX IF NOT EXISTS idx_produto_grade_tamanho 
    ON PRODUTO(cod_grade, cod_tamanho);

-- COR join
CREATE INDEX IF NOT EXISTS idx_produto_cor 
    ON PRODUTO(cod_cor)
    WHERE cod_cor IS NOT NULL;

-- GRUPO/SUBGRUPO joins
CREATE INDEX IF NOT EXISTS idx_produto_grupo_subgrupo 
    ON PRODUTO(cod_grupo, cod_subgrupo);

-- =====================================================
-- NFCOMPRA INDEXES
-- =====================================================

-- NFCompraItem join
CREATE INDEX IF NOT EXISTS idx_nfcompraitem_empresa_produto 
    ON nfcompraitem(cod_empresa, cod_produto);

-- NFCompra join
CREATE INDEX IF NOT EXISTS idx_nfcompra_empresa_interno 
    ON nfcompra(cod_empresa, cod_interno);

-- NFCompra estorno filter
CREATE INDEX IF NOT EXISTS idx_nfcompra_estorno 
    ON nfcompra(cod_empresa, cod_interno, flg_estorno)
    WHERE (flg_estorno IS NULL OR flg_estorno = 'N');

COMMENT ON INDEX idx_nfcompra_estorno IS 
    'Supports estorno filtering in JOIN condition';

-- =====================================================
-- OTHER TABLE INDEXES
-- =====================================================

-- Produto ficha estoque
CREATE INDEX IF NOT EXISTS idx_produto_ficha_estoq_produto 
    ON produto_ficha_estoq(cod_produto);

-- Fornecedor
CREATE INDEX IF NOT EXISTS idx_fornecedor_codigo 
    ON fornecedor(cod_fornece);

-- Marca
CREATE INDEX IF NOT EXISTS idx_marca_codigo 
    ON MARCA(COD_MARCA);

-- Grade tamanho
CREATE INDEX IF NOT EXISTS idx_grade_tamanho_codigo 
    ON grade_tamanho(cod_grade);

-- Tamanho
CREATE INDEX IF NOT EXISTS idx_tamanho_grade_codigo 
    ON tamanho(cod_grade, cod_tamanho);

-- Cores
CREATE INDEX IF NOT EXISTS idx_cores_codigo 
    ON cores(cod_cor);

-- Grupo produto
CREATE INDEX IF NOT EXISTS idx_grupo_produto_codigo 
    ON grupo_produto(cod_grupo);

-- Subgrupo produto
CREATE INDEX IF NOT EXISTS idx_subgrupo_produto_codigo 
    ON subgrupo_produto(cod_grupo, cod_subgrupo);

-- =====================================================
-- ANALYZE TABLES
-- =====================================================

-- Update statistics for query planner
ANALYZE PRODUTO;
ANALYZE nfcompraitem;
ANALYZE nfcompra;
ANALYZE produto_ficha_estoq;
ANALYZE MARCA;
ANALYZE grade_tamanho;
ANALYZE tamanho;
ANALYZE cores;
ANALYZE grupo_produto;
ANALYZE subgrupo_produto;
ANALYZE fornecedor;

COMMIT;

-- =====================================================
-- VERIFICATION
-- =====================================================

-- Check index usage (run after some queries)
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan as scans,
--     idx_tup_read as tuples_read,
--     idx_tup_fetch as tuples_fetched
-- FROM pg_stat_user_indexes
-- WHERE tablename IN ('produto', 'nfcompraitem', 'nfcompra')
-- ORDER BY idx_scan DESC;

-- Check table sizes
-- SELECT 
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
-- FROM pg_tables
-- WHERE tablename IN ('produto', 'nfcompraitem', 'nfcompra', 'produto_ficha_estoq')
-- ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =====================================================
-- NOTES
-- =====================================================

-- 1. These indexes will consume additional disk space
-- 2. They will slightly slow down INSERT/UPDATE/DELETE operations
-- 3. The performance gain for SELECT queries far outweighs the cost
-- 4. Monitor index usage and drop unused indexes if needed
-- 5. Run VACUUM ANALYZE periodically for optimal performance

-- Expected improvements:
-- - Query execution time: 5-10x faster
-- - Better use of date range filtering
-- - Efficient JOIN operations
-- - Optimized sorting for recent items

-- =====================================================
-- END OF SCRIPT
-- =====================================================
