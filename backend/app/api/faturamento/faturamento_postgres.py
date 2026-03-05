from app.db_postgres.connection import CursorFromConnectionFromPool
from typing import List, Dict, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class FaturamentoPostgres:
    """
    Faturamento queries based on nota_fiscal and item_nf tables.
    Faturamento is líquido (net) - returned products should not appear or be shown as reversed.
    Based on document: Faturamento is generated exclusively by Nota Fiscal.
    """
    
    @classmethod
    def get_faturamento_by_brand(cls, data_ini: str, data_fim: str) -> List[Dict]:
        """
        Get faturamento grouped by brand (marca).
        Returns net sales (vlr_total - desc_rat) per brand.
        """
        try:
            logger.info(f"get_faturamento_by_brand called with data_ini={data_ini}, data_fim={data_fim}")
            with CursorFromConnectionFromPool() as cursor:
                # First, check if there's any data at all for this period (without filters)
                cursor.execute('''
                    SELECT COUNT(*) as total_count
                    FROM nota_fiscal nf
                    WHERE nf.dat_emissao::date >= %s::date
                      AND nf.dat_emissao::date <= %s::date
                ''', (data_ini, data_fim))
                if cursor.closed:
                    raise RuntimeError("Cursor was closed unexpectedly after first query")
                total_count = cursor.fetchone()[0]
                logger.info(f"Total invoices in period: {total_count}")
                
                if total_count == 0:
                    logger.warning(f"No invoices found for period {data_ini} to {data_fim}")
                    return []
                
                # Check how many are filtered out
                cursor.execute('''
                    SELECT 
                        COUNT(*) FILTER (WHERE nf.flg_cancelado = 'S') as canceled_count,
                        COUNT(*) FILTER (WHERE nf.cod_grupo_operacoes = 6) as devolucao_count
                    FROM nota_fiscal nf
                    WHERE nf.dat_emissao::date >= %s::date
                      AND nf.dat_emissao::date <= %s::date
                ''', (data_ini, data_fim))
                if cursor.closed:
                    raise RuntimeError("Cursor was closed unexpectedly after second query")
                filter_counts = cursor.fetchone()
                logger.info(f"Canceled invoices: {filter_counts[0]}, Devoluções: {filter_counts[1]}")
                
                # First, get totals for market share calculation
                cursor.execute('''
                    SELECT 
                        SUM(i.vlr_total) as total_bruto_all,
                        SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                            CASE 
                                WHEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                ) > 1.00
                                THEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                )
                                ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                            END
                        ) as total_lucro_all
                    FROM nota_fiscal nf
                    JOIN item_nf i ON i.nf_interno = nf.nf_interno
                    JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
                    WHERE nf.dat_emissao::date >= %s::date
                      AND nf.dat_emissao::date <= %s::date
                      AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                      AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                ''', (data_ini, data_fim))
                try:
                    if cursor.closed:
                        raise RuntimeError("Cursor was closed unexpectedly after third query")
                    totals = cursor.fetchone()
                    if totals is None:
                        logger.warning("No totals returned from query, using defaults")
                        total_bruto_all = 0.0
                        total_lucro_all = 0.0
                    else:
                        total_bruto_all = float(totals[0]) if totals[0] is not None else 0.0
                        total_lucro_all = float(totals[1]) if totals[1] is not None else 0.0
                except Exception as fetch_error:
                    import psycopg2
                    if isinstance(fetch_error, psycopg2.InterfaceError) and "cursor already closed" in str(fetch_error):
                        logger.error(f"Cursor was closed before fetchone() could complete. This may indicate a database connection issue.")
                        raise RuntimeError(f"Database cursor was closed unexpectedly. This may indicate a connection pool issue or database error. Original error: {str(fetch_error)}")
                    raise
                logger.info(f"Total bruto all: {total_bruto_all}, Total lucro all: {total_lucro_all}")
                
                # Don't return early based on totals - let the brand query run
                # Even if totals are 0, there might be brands to show
                
                # Now get brand data
                cursor.execute('''
                    SELECT 
                        m.cod_marca,
                        m.nom_marca,
                        COUNT(DISTINCT nf.nf_interno) as total_notas,
                        COUNT(i.cod_sequencial) as total_itens,
                        SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) as vlr_liquido_total,
                        SUM(i.vlr_total) as vlr_bruto_total,
                        SUM(COALESCE(i.desc_rat, 0)) as total_descontos,
                        SUM(i.qtd_produto * 
                            CASE 
                                WHEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                ) > 1.00
                                THEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                )
                                ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                            END
                        ) as custo_total,
                        SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                            CASE 
                                WHEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                ) > 1.00
                                THEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                )
                                ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                            END
                        ) as margem_total,
                        SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                            CASE 
                                WHEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                ) > 1.00
                                THEN GREATEST(
                                    COALESCE(p.vlr_custo_bruto_medio, 0), 
                                    COALESCE(p.vlr_custo_medio, 0), 
                                    COALESCE(p.vlr_custo_aquis, 0)
                                )
                                ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                            END
                        ) as lucro_total,
                        CASE 
                            WHEN SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) > 0 
                            THEN (SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                                CASE 
                                    WHEN GREATEST(
                                        COALESCE(p.vlr_custo_bruto_medio, 0), 
                                        COALESCE(p.vlr_custo_medio, 0), 
                                        COALESCE(p.vlr_custo_aquis, 0)
                                    ) > 1.00
                                    THEN GREATEST(
                                        COALESCE(p.vlr_custo_bruto_medio, 0), 
                                        COALESCE(p.vlr_custo_medio, 0), 
                                        COALESCE(p.vlr_custo_aquis, 0)
                                    )
                                    ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                                END
                            )) / SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) * 100
                            ELSE 0
                        END as margem_percentual,
                        CASE 
                            WHEN %s > 0 THEN (SUM(i.vlr_total) / %s * 100)
                            ELSE 0
                        END as mkt_share_bruto,
                        CASE 
                            WHEN %s > 0 THEN ((SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                                CASE 
                                    WHEN GREATEST(
                                        COALESCE(p.vlr_custo_bruto_medio, 0), 
                                        COALESCE(p.vlr_custo_medio, 0), 
                                        COALESCE(p.vlr_custo_aquis, 0)
                                    ) > 1.00
                                    THEN GREATEST(
                                        COALESCE(p.vlr_custo_bruto_medio, 0), 
                                        COALESCE(p.vlr_custo_medio, 0), 
                                        COALESCE(p.vlr_custo_aquis, 0)
                                    )
                                    ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                                END
                            )) / %s * 100)
                            ELSE 0
                        END as mkt_share_lucro
                    FROM nota_fiscal nf
                    JOIN item_nf i ON i.nf_interno = nf.nf_interno
                    JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
                    JOIN marca m ON m.cod_marca = p.cod_marca
                    WHERE nf.dat_emissao::date >= %s::date
                      AND nf.dat_emissao::date <= %s::date
                      AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                      AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                    GROUP BY m.cod_marca, m.nom_marca
                    ORDER BY vlr_bruto_total DESC
                ''', (total_bruto_all, total_bruto_all, total_lucro_all, total_lucro_all, data_ini, data_fim))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                rows = cursor.fetchall()
                logger.info(f"Query returned {len(rows)} rows")
                for row in rows:
                    results.append(dict(zip(columns, row)))
                logger.info(f"Found {len(results)} brands")
                if len(results) > 0:
                    logger.info(f"First brand: {results[0].get('nom_marca', 'N/A')} - Vlr Bruto: {results[0].get('vlr_bruto_total', 0)}")
                return results
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            logger.error(f"Error in get_faturamento_by_brand: {error_msg}\n{error_traceback}", exc_info=True)
            raise
    
    @classmethod
    def get_faturamento_by_product(cls, data_ini: str, data_fim: str, cod_marca: Optional[int] = None, include_devolucoes_estornos: bool = False) -> List[Dict]:
        """
        Get faturamento grouped by product.
        Returns net sales per product with margins.
        Excludes products that only have devoluções (cod_origem_movto=4 in produto_ficha_estoq) unless include_devolucoes_estornos=True.
        """
        query = '''
            SELECT 
                p.cod_referencia,
                p.cod_cor,
                c.des_cor,
                m.cod_marca,
                m.nom_marca,
                g.des_grupo,
                sg.des_subgrupo,
                -- Get first product name only (not a list), remove size suffix if present
                -- Remove trailing space + number(s) pattern (e.g., "TENIS ADIDAS VS PACE BRANCO 39" -> "TENIS ADIDAS VS PACE BRANCO")
                -- Use SUBSTRING to remove trailing numbers more reliably
                TRIM(
                    REGEXP_REPLACE(
                        MIN(p.des_produto),
                        E'\\s+\\d+$',  -- Remove trailing space + one or more digits
                        ''
                    )
                ) as des_produto,
                COUNT(DISTINCT nf.nf_interno) as total_notas,
                COUNT(i.cod_sequencial) as total_itens,
                SUM(i.qtd_produto) as qtd_total,
                SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) as vlr_liquido_total,
                SUM(i.vlr_total) as vlr_bruto_total,
                SUM(COALESCE(i.desc_rat, 0)) as total_descontos,
                AVG(
                    CASE 
                        WHEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        ) > 1.00
                        THEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        )
                        ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                    END
                ) as custo_medio,
                SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                    CASE 
                        WHEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        ) > 1.00
                        THEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        )
                        ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                    END
                ) as margem_total,
                SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                    CASE 
                        WHEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        ) > 1.00
                        THEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        )
                        ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                    END
                ) as lucro_total,
                CASE 
                    WHEN SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) > 0 
                    THEN (SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                        CASE 
                            WHEN GREATEST(
                                COALESCE(p.vlr_custo_bruto_medio, 0), 
                                COALESCE(p.vlr_custo_medio, 0), 
                                COALESCE(p.vlr_custo_aquis, 0)
                            ) > 1.00
                            THEN GREATEST(
                                COALESCE(p.vlr_custo_bruto_medio, 0), 
                                COALESCE(p.vlr_custo_medio, 0), 
                                COALESCE(p.vlr_custo_aquis, 0)
                            )
                            ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                        END
                    )) / SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) * 100
                    ELSE 0
                END as margem_percentual,
                -- Flag to indicate if default cost (vlr_venda1/2) was used
                BOOL_OR(
                    GREATEST(
                        COALESCE(p.vlr_custo_bruto_medio, 0), 
                        COALESCE(p.vlr_custo_medio, 0), 
                        COALESCE(p.vlr_custo_aquis, 0)
                    ) <= 1.00
                ) as custo_is_default,
                STRING_AGG(DISTINCT 
                    CASE 
                        WHEN nf.cod_usuario IS NOT NULL AND nf.cod_usuario != 0 AND u_nf.nom_usuario IS NOT NULL AND TRIM(COALESCE(u_nf.nom_usuario, '')) != ''
                        THEN u_nf.nom_usuario
                        WHEN i.cod_vendedor != 0 AND u.nom_usuario IS NOT NULL AND TRIM(COALESCE(u.nom_usuario, '')) != '' 
                        THEN u.nom_usuario
                        ELSE 'E-commerce'
                    END, ', ' ORDER BY 
                    CASE 
                        WHEN nf.cod_usuario IS NOT NULL AND nf.cod_usuario != 0 AND u_nf.nom_usuario IS NOT NULL AND TRIM(COALESCE(u_nf.nom_usuario, '')) != ''
                        THEN u_nf.nom_usuario
                        WHEN i.cod_vendedor != 0 AND u.nom_usuario IS NOT NULL AND TRIM(COALESCE(u.nom_usuario, '')) != '' 
                        THEN u.nom_usuario
                        ELSE 'E-commerce'
                    END
                ) as nom_vendedor
            FROM nota_fiscal nf
            JOIN item_nf i ON i.nf_interno = nf.nf_interno
            JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
            JOIN marca m ON m.cod_marca = p.cod_marca
            LEFT JOIN grupo_produto g ON g.cod_grupo = p.cod_grupo
            LEFT JOIN subgrupo_produto sg ON sg.cod_grupo = p.cod_grupo AND sg.cod_subgrupo = p.cod_subgrupo
            LEFT JOIN cores c ON c.cod_cor = p.cod_cor
            LEFT JOIN usuarios u ON u.cod_usuario = i.cod_vendedor
            LEFT JOIN usuarios u_nf ON u_nf.cod_usuario = nf.cod_usuario
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
              -- Exclude canceled invoices
              AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
              -- Exclude devoluções (cod_grupo_operacoes = 6) unless include_devolucoes_estornos is True
              AND (
                (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                OR (%s::boolean)  -- Include devoluções if flag is True
              )
        '''
        
        params = [data_ini, data_fim, include_devolucoes_estornos]
        if cod_marca:
            query += ' AND m.cod_marca = %s'
            params.append(cod_marca)
        
        query += '''
            GROUP BY p.cod_referencia, p.cod_cor, c.des_cor, m.cod_marca, m.nom_marca, g.des_grupo, sg.des_subgrupo
            HAVING SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) > 0  -- Only show products with actual sales
        '''
        
        # Additional filter: exclude products that have devoluções in produto_ficha_estoq (unless flag is True)
        # Products with cod_origem_movto=4 (Devolução) should be excluded unless checkbox is checked
        if not include_devolucoes_estornos:
            query += '''
            AND NOT EXISTS (
                -- Exclude if product has devoluções (cod_origem_movto=4) in produto_ficha_estoq for this date range
                SELECT 1 FROM produto_ficha_estoq pfe_dev
                JOIN produto p_dev ON p_dev.cod_produto = pfe_dev.cod_produto AND p_dev.cod_empresa = '1'
                WHERE p_dev.cod_referencia = p.cod_referencia
                  AND p_dev.cod_cor = p.cod_cor
                  AND pfe_dev.data::date >= %s::date
                  AND pfe_dev.data::date <= %s::date
                  AND pfe_dev.cod_origem_movto = 4  -- Devolução
            )
            '''
            params.extend([data_ini, data_fim])
        
        query += '''
            ORDER BY vlr_liquido_total DESC
        '''
        
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            logger.info(f"Found {len(results)} brands")
            return results
    
    @classmethod
    def get_faturamento_by_size(cls, data_ini: str, data_fim: str, cod_marca: Optional[int] = None) -> List[Dict]:
        """
        Get faturamento grouped by size (tamanho/grade).
        """
        query = '''
            SELECT 
                t.des_tamanho,
                g.des_grade,
                COUNT(DISTINCT nf.nf_interno) as total_notas,
                COUNT(i.cod_sequencial) as total_itens,
                SUM(i.qtd_produto) as qtd_total,
                SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) as vlr_liquido_total
            FROM nota_fiscal nf
            JOIN item_nf i ON i.nf_interno = nf.nf_interno
            JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
            JOIN marca m ON m.cod_marca = p.cod_marca
            LEFT JOIN tamanho t ON t.cod_grade = p.cod_grade AND t.cod_tamanho = p.cod_tamanho
            LEFT JOIN grade_tamanho g ON g.cod_grade = p.cod_grade
        '''
        
        params = [data_ini, data_fim]
        where_clause = '''
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
        '''
        
        if cod_marca:
            where_clause += ' AND m.cod_marca = %s'
            params.append(cod_marca)
        
        query += where_clause + '''
            GROUP BY t.des_tamanho, g.des_grade
            ORDER BY vlr_liquido_total DESC
        '''
        
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            logger.info(f"Found {len(results)} brands")
            return results
    
    @classmethod
    def get_faturamento_by_collection(cls, data_ini: str, data_fim: str) -> List[Dict]:
        """
        Get faturamento grouped by collection (winter/summer based on dat_emissao).
        Winter: months 6-8 (June-August in Brazil)
        Summer: months 12-2 (December-February in Brazil)
        """
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN EXTRACT(MONTH FROM nf.dat_emissao) IN (6, 7, 8) THEN 'Inverno'
                        WHEN EXTRACT(MONTH FROM nf.dat_emissao) IN (12, 1, 2) THEN 'Verão'
                        ELSE 'Outras'
                    END as colecao,
                    COUNT(DISTINCT nf.nf_interno) as total_notas,
                    COUNT(i.cod_sequencial) as total_itens,
                    SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) as vlr_liquido_total
                FROM nota_fiscal nf
                JOIN item_nf i ON i.nf_interno = nf.nf_interno
                WHERE nf.dat_emissao::date >= %s::date
                  AND nf.dat_emissao::date <= %s::date
                  AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                  AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                GROUP BY colecao
                ORDER BY vlr_liquido_total DESC
            ''', (data_ini, data_fim))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            logger.info(f"Found {len(results)} brands")
            return results
    
    @classmethod
    def get_products_promotion_only(cls, data_ini: str, data_fim: str) -> List[Dict]:
        """
        Get products that only sell on promotion (have desc_rat > 0).
        These should be flagged for alerts - slow products that need promotion.
        """
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''
                SELECT 
                    p.cod_produto,
                    p.des_produto,
                    p.cod_referencia,
                    m.nom_marca,
                    COUNT(DISTINCT nf.nf_interno) as total_notas,
                    SUM(i.qtd_produto) as qtd_total,
                    SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) as vlr_liquido_total,
                    SUM(COALESCE(i.desc_rat, 0)) as total_descontos,
                    CASE 
                        WHEN SUM(i.vlr_total) > 0 
                        THEN SUM(COALESCE(i.desc_rat, 0)) / SUM(i.vlr_total) * 100
                        ELSE 0
                    END as percentual_desconto
                FROM nota_fiscal nf
                JOIN item_nf i ON i.nf_interno = nf.nf_interno
                JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
                JOIN marca m ON m.cod_marca = p.cod_marca
                WHERE nf.dat_emissao::date >= %s::date
                  AND nf.dat_emissao::date <= %s::date
                  AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                  AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                  AND i.desc_rat > 0
                GROUP BY p.cod_produto, p.des_produto, p.cod_referencia, m.nom_marca
                HAVING COUNT(DISTINCT CASE WHEN i.desc_rat = 0 THEN nf.nf_interno END) = 0
                ORDER BY total_descontos DESC
            ''', (data_ini, data_fim))
    
    @classmethod
    def get_movimentos_by_referencia_cor(cls, cod_referencia: str, cod_cor: int, data_ini: str, data_fim: str, include_devolucoes_estornos: bool = False) -> List[Dict]:
        """
        Get detailed movimentos by referencia and cor, using produto_ficha_estoq (like Levantamentos).
        Includes devoluções (cod_origem_movto=4) shown as 'devolução E' only if include_devolucoes_estornos=True.
        Links to nota_fiscal when available to get sales value.
        Filters out canceled movements (same cod_movto with both E and S).
        """
        # Convert boolean to PostgreSQL boolean (ensure it's a proper boolean)
        include_devolucoes_estornos_pg = bool(include_devolucoes_estornos)
        logger.info(f"Loading movimentos for {cod_referencia}, cor {cod_cor}, include_devolucoes_estornos={include_devolucoes_estornos_pg}")
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''
                SELECT 
                    p.cod_produto,
                    p.des_produto,
                    t.des_tamanho,
                    g.des_grade,
                    pfe.data as dat_emissao,
                    pfe.cod_movto,
                    pfe.tipo_movto,
                    pfe.qtd_movto as qtd_produto,
                    pfe.cod_origem_movto,
                    CASE 
                        WHEN pfe.cod_origem_movto = 4 THEN 'Devolução'
                        WHEN pfe.cod_origem_movto = 2 THEN 'Emissão Nota Fiscal'
                        WHEN pfe.cod_origem_movto = 3 THEN 'Requisição'
                        WHEN pfe.cod_origem_movto = 7 THEN 'Ent. Proc. Notas'
                        WHEN pfe.cod_origem_movto = 9 THEN 'Frente de Caixa'
                        WHEN pfe.cod_origem_movto = 12 THEN 'Estorno Proc. Notas'
                        WHEN pfe.cod_origem_movto = 15 THEN 'Condicional'
                        ELSE 'Outro'
                    END as origem_nome,
                    -- Get value from nota_fiscal: sum all items for this NF with same referencia+cor
                    -- Completely independent subquery - doesn't rely on main join
                    -- All rows for same date + referencia + cor will get same vlr_liquido
                    CASE 
                        WHEN pfe.cod_origem_movto IN (2, 9) THEN
                            COALESCE((
                                SELECT SUM(i3.vlr_total - COALESCE(i3.desc_rat, 0))
                                FROM nota_fiscal nf3
                                JOIN item_nf i3 ON i3.nf_interno = nf3.nf_interno
                                JOIN produto p3 ON p3.cod_produto = i3.cod_produto AND p3.cod_empresa = i3.cod_empresa
                                WHERE nf3.dat_emissao::date = pfe.data::date
                                  AND p3.cod_referencia = p.cod_referencia
                                  AND p3.cod_cor = p.cod_cor
                                  AND (nf3.flg_cancelado IS NULL OR nf3.flg_cancelado != 'S')
                                  AND (nf3.cod_grupo_operacoes IS NULL OR nf3.cod_grupo_operacoes != 6)
                                GROUP BY nf3.nf_interno
                                ORDER BY nf3.nf_interno
                                LIMIT 1
                            ), 0)
                        ELSE 0
                    END as vlr_liquido,
                    -- Get NF from independent subquery (same logic as vlr_liquido)
                    CASE 
                        WHEN pfe.cod_origem_movto IN (2, 9) THEN
                            COALESCE((
                                SELECT nf3.nf_interno
                                FROM nota_fiscal nf3
                                JOIN item_nf i3 ON i3.nf_interno = nf3.nf_interno
                                JOIN produto p3 ON p3.cod_produto = i3.cod_produto AND p3.cod_empresa = i3.cod_empresa
                                WHERE nf3.dat_emissao::date = pfe.data::date
                                  AND p3.cod_referencia = p.cod_referencia
                                  AND p3.cod_cor = p.cod_cor
                                  AND (nf3.flg_cancelado IS NULL OR nf3.flg_cancelado != 'S')
                                  AND (nf3.cod_grupo_operacoes IS NULL OR nf3.cod_grupo_operacoes != 6)
                                GROUP BY nf3.nf_interno
                                ORDER BY nf3.nf_interno
                                LIMIT 1
                            ), NULL)
                        ELSE NULL
                    END as nf_interno,
                    -- Get vendedor from nota_fiscal if available
                    -- Simplified: use main join if available, otherwise fallback to subquery
                    CASE 
                        WHEN pfe.cod_origem_movto IN (2, 9) THEN
                            CASE 
                                WHEN nf.nf_interno IS NOT NULL THEN
                                    CASE 
                                        WHEN nf.cod_usuario IS NOT NULL AND nf.cod_usuario != 0 AND u_nf.nom_usuario IS NOT NULL AND TRIM(COALESCE(u_nf.nom_usuario, '')) != ''
                                        THEN u_nf.nom_usuario
                                        WHEN i.cod_vendedor IS NOT NULL AND i.cod_vendedor != 0 AND u.nom_usuario IS NOT NULL AND TRIM(COALESCE(u.nom_usuario, '')) != '' 
                                        THEN u.nom_usuario
                                        ELSE 'E-commerce'
                                    END
                                ELSE 'E-commerce'
                            END
                        WHEN pfe.cod_origem_movto = 4 THEN 'Devolução'
                        ELSE 'E-commerce'
                    END as nom_vendedor
                FROM produto_ficha_estoq pfe
                JOIN produto p ON p.cod_produto = pfe.cod_produto AND p.cod_empresa = '1'
                LEFT JOIN tamanho t ON t.cod_grade = p.cod_grade AND t.cod_tamanho = p.cod_tamanho
                LEFT JOIN grade_tamanho g ON g.cod_grade = p.cod_grade
                -- Join to item_nf and nota_fiscal for sales (cod_origem_movto 2 or 9)
                -- Match by specific produto first (more accurate), then we'll aggregate by NF in subquery
                LEFT JOIN item_nf i ON i.cod_produto = p.cod_produto
                    AND i.cod_empresa = p.cod_empresa
                    AND (pfe.cod_origem_movto = 2 OR pfe.cod_origem_movto = 9)
                LEFT JOIN nota_fiscal nf ON nf.nf_interno = i.nf_interno
                    AND nf.dat_emissao::date = pfe.data::date
                    AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                    AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                LEFT JOIN usuarios u ON u.cod_usuario = i.cod_vendedor
                LEFT JOIN usuarios u_nf ON u_nf.cod_usuario = nf.cod_usuario
                WHERE p.cod_referencia = %s
                  AND p.cod_cor = %s
                  AND pfe.data::date >= %s::date
                  AND pfe.data::date <= %s::date
                  -- Include relevant movimento origins (like Levantamentos)
                  -- Filter devoluções (4) and estornos (12) based on include_devolucoes_estornos flag
                  AND (
                    pfe.cod_origem_movto IN (2, 3, 7, 9, 15)  -- Always include sales and other movements
                    OR (pfe.cod_origem_movto IN (4, 12) AND %s::boolean)  -- Include devoluções/estornos only if flag is True
                  )
                ORDER BY pfe.data DESC, t.des_tamanho
            ''', (cod_referencia, cod_cor, data_ini, data_fim, include_devolucoes_estornos_pg))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            # Filter out canceled movements: same cod_movto with both E and S
            # Group by cod_movto and check if both E and S exist
            movto_types = {}  # {cod_movto: set(['E', 'S'])}
            for row in results:
                cod_movto = row.get('cod_movto')
                tipo_movto = row.get('tipo_movto')
                if cod_movto:
                    if cod_movto not in movto_types:
                        movto_types[cod_movto] = set()
                    movto_types[cod_movto].add(tipo_movto)
            
            # Filter out movements where same cod_movto has both E and S (canceled)
            canceled_movtos = {cod_movto for cod_movto, types in movto_types.items() 
                              if 'E' in types and 'S' in types}
            
            filtered_results = [row for row in results 
                              if row.get('cod_movto') not in canceled_movtos]
            
            logger.info(f"Found {len(results)} movimentos for referencia {cod_referencia}, cor {cod_cor}, "
                       f"filtered {len(results) - len(filtered_results)} canceled movements")
            return filtered_results
