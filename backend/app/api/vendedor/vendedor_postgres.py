from app.db_postgres.connection import CursorFromConnectionFromPool
from typing import List, Dict, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class VendedorPostgres:
    """
    Vendedor queries for Metas (targets) and Vendas (sales).
    Uses COMISSAO table as single source of truth (PROJECT_RULES Section 9.1).
    base_calc_comissao is the net revenue after returns, cancellations and adjustments.
    """
    
    @classmethod
    def get_vendedores_ativos(cls) -> List[Dict]:
        """
        Get list of all salespersons from USUARIOS table.
        Loads cod_usuario and nom_usuario from usuarios table.
        """
        try:
            with CursorFromConnectionFromPool() as cursor:
                # Simplified query - match the pattern used in comissao_postgres.py
                cursor.execute('''
                    SELECT 
                        u.cod_usuario as cod_vendedor,
                        u.nom_usuario as nom_vendedor,
                        CASE 
                            WHEN u.flg_ativo = 'S' THEN true 
                            ELSE false 
                        END as ativo
                    FROM USUARIOS u
                    WHERE u.cod_usuario IS NOT NULL
                    ORDER BY u.nom_usuario
                ''')
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    # Ensure all required fields are present
                    if row_dict.get('cod_vendedor') is not None:
                        results.append(row_dict)
                return results
        except Exception as e:
            logger.error(f"Error in get_vendedores_ativos: {str(e)}", exc_info=True)
            # Try alternative query if first fails
            try:
                logger.info("Attempting alternative query with lowercase table name")
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute('''
                        SELECT 
                            cod_usuario as cod_vendedor,
                            nom_usuario as nom_vendedor,
                            CASE 
                                WHEN flg_ativo = 'S' THEN true 
                                ELSE false 
                            END as ativo
                        FROM usuarios
                        WHERE cod_usuario IS NOT NULL
                        ORDER BY nom_usuario
                    ''')
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        if row_dict.get('cod_vendedor') is not None:
                            results.append(row_dict)
                    return results
            except Exception as e2:
                logger.error(f"Alternative query also failed: {str(e2)}", exc_info=True)
                raise e  # Raise original error
    
    @classmethod
    def get_vendas_by_day(cls, cod_vendedor: int, data_ini: str, data_fim: str) -> List[Dict]:
        """
        Get sales by day for a specific vendor.
        Uses COMISSAO table as single source of truth.
        Returns net sales (base_calc_comissao) - already excludes returns, cancellations, adjustments.
        """
        try:
            with CursorFromConnectionFromPool() as cursor:
                # IMPORTANT: Use COMISSAO table as single source of truth
                # base_calc_comissao is net revenue after returns, cancellations and adjustments
                cursor.execute('''
                    SELECT 
                        A.dat_emissao::date as data_venda,
                        A.cod_origem as nf_interno,
                        COALESCE(nf.numero::text, A.cod_origem::text, '') as num_nf,
                        nf.cod_cliente as cod_cliente,
                        CASE
                            WHEN nf.cod_cliente IS NULL OR nf.cod_cliente = 0 THEN 'Consumidor Final'
                            ELSE COALESCE(cl.fan_cliente, cl.raz_cliente, nf.cod_cliente::text)
                        END as nom_cliente,
                        COUNT(*) as total_itens,
                        NULL as qtd_total,
                        SUM(A.base_calc_comissao) as vlr_liquido_total,
                        SUM(A.base_calc_comissao) as vlr_bruto_total,
                        SUM(COALESCE(A.vlr_credito, 0)) as total_descontos
                    FROM COMISSAO A
                    LEFT OUTER JOIN USUARIOS AB ON (A.cod_vendedor = AB.cod_usuario)
                    LEFT OUTER JOIN nota_fiscal nf ON nf.nf_interno = A.cod_origem
                    LEFT OUTER JOIN cliente cl ON cl.cod_cliente = nf.cod_cliente
                    WHERE A.dat_emissao::date >= %s::date
                      AND A.dat_emissao::date <= %s::date
                      AND A.cod_vendedor = %s
                    GROUP BY A.dat_emissao::date, A.cod_origem, nf.numero, nf.cod_cliente, cl.fan_cliente, cl.raz_cliente
                    ORDER BY A.dat_emissao::date DESC, A.cod_origem
                ''', (data_ini, data_fim, cod_vendedor))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                # Return empty list if no results (don't raise error)
                return results
        except Exception as e:
            logger.error(f"Error in get_vendas_by_day: {str(e)}", exc_info=True)
            # Return empty list instead of raising for date ranges with no data
            return []
    
    @classmethod
    def get_vendas_items_by_nf(cls, nf_interno: int) -> List[Dict]:
        """
        Get items for a specific invoice (NF).
        """
        try:
            with CursorFromConnectionFromPool() as cursor:
                # Use lowercase table names (matching faturamento_postgres.py pattern)
                # Removed vlr_unitario as column doesn't exist - calculate from vlr_total and qtd_produto if needed
                cursor.execute('''
                    SELECT 
                        i.cod_sequencial,
                        p.cod_produto,
                        p.des_produto,
                        p.cod_referencia,
                        COALESCE(m.nom_marca, '') as nom_marca,
                        i.qtd_produto,
                        CASE 
                            WHEN i.qtd_produto > 0 THEN i.vlr_total / i.qtd_produto
                            ELSE 0
                        END as vlr_unitario,
                        i.vlr_total,
                        COALESCE(i.desc_rat, 0) as desc_rat,
                        i.vlr_total - COALESCE(i.desc_rat, 0) as vlr_liquido
                    FROM item_nf i
                    JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
                    LEFT JOIN marca m ON m.cod_marca = p.cod_marca
                    WHERE i.nf_interno = %s
                    ORDER BY i.cod_sequencial
                ''', (nf_interno,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                # Return empty list if no items found (don't raise error)
                return results
        except Exception as e:
            logger.error(f"Error in get_vendas_items_by_nf: {str(e)}", exc_info=True)
            # Return empty list instead of raising for invoices with no items
            return []
    
    @classmethod
    def get_vendedores_com_vendas_mes(cls, ano: int, mes: int) -> List[Dict]:
        """
        Get all sellers that have sales in the given month/year.
        Returns cod_vendedor, nom_vendedor, total_vendas for each.
        """
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute('''
                    SELECT 
                        A.cod_vendedor,
                        MAX(AB.nom_usuario) as nom_vendedor,
                        SUM(A.base_calc_comissao) as total_vendas,
                        COUNT(DISTINCT A.cod_origem) as total_notas
                    FROM COMISSAO A
                    LEFT OUTER JOIN USUARIOS AB ON (A.cod_vendedor = AB.cod_usuario)
                    WHERE EXTRACT(YEAR FROM A.dat_emissao) = %s
                      AND EXTRACT(MONTH FROM A.dat_emissao) = %s
                    GROUP BY A.cod_vendedor
                    HAVING SUM(A.base_calc_comissao) > 0
                    ORDER BY SUM(A.base_calc_comissao) DESC
                ''', (ano, mes))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_vendedores_com_vendas_mes: {str(e)}", exc_info=True)
            return []

    @classmethod
    def get_vendas_diarias_mes(cls, cod_vendedor: int, ano: int, mes: int) -> List[Dict]:
        """
        Get daily sales for a seller in a given month.
        Returns day number and daily total (not cumulative).
        """
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute('''
                    SELECT 
                        EXTRACT(DAY FROM A.dat_emissao)::integer as dia,
                        SUM(A.base_calc_comissao) as vlr_dia
                    FROM COMISSAO A
                    WHERE EXTRACT(YEAR FROM A.dat_emissao) = %s
                      AND EXTRACT(MONTH FROM A.dat_emissao) = %s
                      AND A.cod_vendedor = %s
                    GROUP BY EXTRACT(DAY FROM A.dat_emissao)
                    ORDER BY dia
                ''', (ano, mes, cod_vendedor))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_vendas_diarias_mes: {str(e)}", exc_info=True)
            return []

    @classmethod
    def get_vendas_monthly_summary(cls, cod_vendedor: int, ano: int) -> List[Dict]:
        """
        Get monthly sales summary for a vendor (for Metas comparison).
        Uses COMISSAO table as single source of truth.
        base_calc_comissao is net revenue after returns, cancellations and adjustments.
        """
        try:
            with CursorFromConnectionFromPool() as cursor:
                # IMPORTANT: Use COMISSAO table as single source of truth
                # base_calc_comissao already excludes canceled invoices and returns
                cursor.execute('''
                    SELECT 
                        EXTRACT(MONTH FROM A.dat_emissao)::integer as mes,
                        TO_CHAR(A.dat_emissao, 'YYYY-MM') as mes_ano,
                        COUNT(DISTINCT A.cod_origem) as total_notas,
                        SUM(A.base_calc_comissao) as vlr_liquido_total
                    FROM COMISSAO A
                    WHERE EXTRACT(YEAR FROM A.dat_emissao) = %s
                      AND A.cod_vendedor = %s
                    GROUP BY EXTRACT(MONTH FROM A.dat_emissao), TO_CHAR(A.dat_emissao, 'YYYY-MM')
                    ORDER BY mes
                ''', (ano, cod_vendedor))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
        except Exception as e:
            logger.error(f"Error in get_vendas_monthly_summary: {str(e)}", exc_info=True)
            raise

    @classmethod
    def get_table_columns(cls, table_name: str) -> List[str]:
        """Get column names for a table (schema discovery helper)."""
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position",
                    (table_name,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting columns for {table_name}: {str(e)}")
            return []
