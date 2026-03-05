from app.db_postgres.connection import CursorFromConnectionFromPool
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class LevantamentoPostgres:
    @classmethod
    def load_estoque_from_db(cls, dat_cadastro_ini, dat_cadastro_fim, cod_marca):
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''
                select pro.cod_grupo, gu.des_grupo, pro.cod_subgrupo, su.des_subgrupo,
            pro.cod_produto, pro.des_produto, pro.cod_barra, pro.cod_referencia,
            sum(it.qtd_produto) as qtd, pro.saldo_estoque,
            pro.vlr_custo_bruto, pro.vlr_custo_aquis, pro.vlr_venda1, sum(it.vlr_total) as total,
            pro.cod_grade, g.des_grade,
            pro.cod_tamanho, t.des_tamanho,
            pro.cod_cor, c.des_cor,
            pro.dat_cadastro,pro.dat_ultcompra, cb.cod_fornece, 
            f.raz_fornece, f.fan_fornece,
            m.cod_marca, m.nom_marca,
            pfe.tipo_movto, pfe.qtd_movto, pfe.data as data_movto, pfe.cod_movto, pfe.cod_origem_movto
    FROM PRODUTO pro
             LEFT OUTER JOIN MARCA m ON (m.COD_MARCA = pro.COD_MARCA)
            LEFT OUTER JOIN nfcompraitem it on (pro.cod_empresa = it.cod_empresa and pro.cod_produto = it.cod_produto)
            -- Movimento filtered by date range (for entrada calculations)
            LEFT OUTER JOIN produto_ficha_estoq pfe on (pfe.cod_produto = pro.cod_produto 
                AND pfe.data >= %s 
                AND pfe.data <= %s)
        LEFT OUTER JOIN grupo_produto gu on (gu.cod_grupo = pro.cod_grupo)
            LEFT OUTER JOIN nfcompra cb on (cb.cod_empresa = it.cod_empresa and cb.cod_interno = it.cod_interno)
            left outer join cores c on (c.cod_cor = pro.cod_cor)
             inner join grade_tamanho g on (g.cod_grade = pro.cod_grade)
             inner join tamanho t on (t.cod_grade = pro.cod_grade and t.cod_tamanho = pro.cod_tamanho)
             LEFT OUTER JOIN fornecedor f on (cb.cod_fornece = f.cod_fornece)
            LEFT OUTER JOIN subgrupo_produto su on (su.cod_grupo = pro.cod_grupo and su.cod_subgrupo = pro.cod_subgrupo)
    where pro.cod_empresa = '1'
          -- Filter: Only show products that have movimento within the date range
          and EXISTS (
              SELECT 1 FROM produto_ficha_estoq pfe2 
              WHERE pfe2.cod_produto = pro.cod_produto 
                AND pfe2.data >= %s 
                AND pfe2.data <= %s
          )
          and (cb.flg_estorno is null or cb.flg_estorno = 'N')
          and m.cod_marca = %s
          and (pro.flg_mestre = 'N' or pro.flg_mestre is null)
    group by pro.cod_grupo, gu.des_grupo, pro.cod_subgrupo, su.des_subgrupo,
                 pro.cod_produto, pro.des_produto,  pro.cod_barra, pro.cod_referencia,
                 pro.vlr_custo_bruto, pro.vlr_custo_aquis, pro.vlr_venda1,
                 pro.cod_grade, g.des_grade, pro.saldo_estoque,
                 pro.cod_tamanho, t.des_tamanho,
                 pro.cod_cor,  c.des_cor,
                 pro.dat_cadastro,pro.dat_ultcompra, cb.cod_fornece,
                 f.raz_fornece, f.fan_fornece,
                 m.cod_marca, m.nom_marca,
                 pfe.tipo_movto, pfe.qtd_movto, data_movto, pfe.cod_movto, pfe.cod_origem_movto
        order by 1, 2, 3, 4''', (dat_cadastro_ini, dat_cadastro_fim, dat_cadastro_ini, dat_cadastro_fim, cod_marca))
            dados_estoque = cursor.fetchall()
        return dados_estoque

    @classmethod
    def load_marcas_from_db(cls) -> List[Dict]:
        """Load distinct marcas (cod_marca, nom_marca) from PostgreSQL for dropdown. Used when MongoDB is empty."""
        with CursorFromConnectionFromPool() as cursor:
            # Try direct table first; fallback to join with produto (same pattern as load_estoque)
            for query in [
                '''SELECT cod_marca, nom_marca FROM marca
                   WHERE cod_marca IS NOT NULL AND (nom_marca IS NOT NULL AND TRIM(COALESCE(nom_marca,'')) != '')
                   ORDER BY nom_marca''',
                '''SELECT DISTINCT m.cod_marca, m.nom_marca FROM produto p
                   JOIN marca m ON (p.cod_marca = m.cod_marca)
                   WHERE p.cod_empresa = '1'
                   ORDER BY m.nom_marca''',
            ]:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    result = [{"cod_marca": r[0], "nom_marca": r[1] or ""} for r in rows]
                    if result:
                        logger.info("load_marcas_from_db: loaded %d marcas from PostgreSQL", len(result))
                        return result
                except Exception as e:
                    logger.debug("load_marcas_from_db query failed: %s", e)
                    continue
        logger.warning("load_marcas_from_db: no marcas found in PostgreSQL")
        return []

    @classmethod
    def get_selling_performance(cls, ano_analise: int = 2023) -> Dict[str, Dict]:
        """
        Calculate selling performance metrics for products grouped by cod_referencia + cod_cor.
        Returns a dictionary with performance scores (0-100) for each reference+color combination.
        
        Metric calculation:
        1. Sales Velocity: Units sold per day since first sale
        2. Recent Trend: Last 30 days vs previous 30 days (to catch products that started fast but stopped)
        3. Normalized Score: Compared to median of all products
        
        Returns:
            {
                "REF123-1": {
                    "score": 75.5,  # 0-100, higher = faster selling
                    "velocity": 2.3,  # units per day
                    "trend": 1.2,  # recent/previous ratio
                    "total_sold": 150,
                    "days_active": 65,
                    "first_sale": "2023-01-15",
                    "last_sale": "2023-03-21"
                }
            }
        """
        try:
            # If no year specified, use most recent year with data (try last 3 years)
            if ano_analise is None:
                current_year = date.today().year
                for year in range(current_year - 1, max(2019, current_year - 4), -1):
                    # Try to find data for this year
                    ano_analise = year
                    break
                if ano_analise is None:
                    ano_analise = 2023  # Fallback
            
            # Calculate date range for analysis year
            data_ini = date(ano_analise, 1, 1)
            data_fim = date(ano_analise, 12, 31)
            
            # Get last 30 days of analysis year for trend calculation
            data_fim_recent = data_fim
            data_ini_recent = data_fim_recent - timedelta(days=30)
            data_fim_previous = data_ini_recent - timedelta(days=1)
            data_ini_previous = data_fim_previous - timedelta(days=30)
            
            with CursorFromConnectionFromPool() as cursor:
                # Get sales data grouped by reference + color
                # Only count actual sales (cod_origem_movto IN 2, 9) and exclude canceled/devoluções
                cursor.execute('''
                    SELECT 
                        p.cod_referencia,
                        p.cod_cor,
                        MIN(p.dat_cadastro)::date as dat_cadastro,
                        MIN(pfe.data)::date as primeira_venda,
                        MAX(pfe.data)::date as ultima_venda,
                        SUM(CASE WHEN pfe.cod_origem_movto IN (2, 9) AND pfe.tipo_movto = 'S' THEN ABS(pfe.qtd_movto) ELSE 0 END) as total_vendido,
                        -- Recent period sales (last 30 days)
                        SUM(CASE 
                            WHEN pfe.cod_origem_movto IN (2, 9) 
                            AND pfe.tipo_movto = 'S'
                            AND pfe.data::date >= %s::date 
                            AND pfe.data::date <= %s::date
                            THEN ABS(pfe.qtd_movto) 
                            ELSE 0 
                        END) as vendas_recentes,
                        -- Previous period sales (30 days before recent)
                        SUM(CASE 
                            WHEN pfe.cod_origem_movto IN (2, 9) 
                            AND pfe.tipo_movto = 'S'
                            AND pfe.data::date >= %s::date 
                            AND pfe.data::date <= %s::date
                            THEN ABS(pfe.qtd_movto) 
                            ELSE 0 
                        END) as vendas_anteriores
                    FROM produto_ficha_estoq pfe
                    JOIN produto p ON p.cod_produto = pfe.cod_produto AND p.cod_empresa = '1'
                    WHERE pfe.data::date >= %s::date
                      AND pfe.data::date <= %s::date
                      AND pfe.cod_origem_movto IN (2, 9)  -- Only sales (Emissão NF and Frente de Caixa)
                      AND pfe.tipo_movto = 'S'  -- Only saída (sales)
                      -- Exclude canceled invoices: check if there's a canceled NF for this date+product
                      AND NOT EXISTS (
                          SELECT 1 
                          FROM item_nf i2
                          JOIN nota_fiscal nf2 ON nf2.nf_interno = i2.nf_interno
                          WHERE i2.cod_produto = p.cod_produto
                            AND i2.cod_empresa = p.cod_empresa
                            AND nf2.dat_emissao::date = pfe.data::date
                            AND (nf2.flg_cancelado = 'S' OR nf2.cod_grupo_operacoes = 6)
                      )
                    GROUP BY p.cod_referencia, p.cod_cor
                    HAVING SUM(CASE WHEN pfe.cod_origem_movto IN (2, 9) AND pfe.tipo_movto = 'S' THEN ABS(pfe.qtd_movto) ELSE 0 END) > 0
                ''', (
                    data_ini_recent, data_fim_recent,  # Recent period
                    data_ini_previous, data_fim_previous,  # Previous period
                    data_ini, data_fim  # Full year
                ))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                if not results:
                    logger.warning(f"No sales data found for year {ano_analise}")
                    return {}
                
                logger.info(f"Found {len(results)} product groups with sales in {ano_analise}")
                
                # Calculate performance metrics for each product
                performance_data = {}
                velocities = []
                
                for row in results:
                    cod_referencia = str(row['cod_referencia']).strip() if row['cod_referencia'] else ''
                    cod_cor = int(row['cod_cor']) if row['cod_cor'] is not None else 0
                    key = f"{cod_referencia}-{cod_cor}"
                    
                    # Debug first few
                    if len(performance_data) < 3:
                        logger.info(f"Processing: ref={cod_referencia}, cor={cod_cor}, key={key}, total_vendido={row.get('total_vendido', 0)}")
                    
                    dat_cadastro = row.get('dat_cadastro')  # Product registration date
                    primeira_venda = row['primeira_venda']
                    ultima_venda = row['ultima_venda']
                    total_vendido = float(row['total_vendido'] or 0)
                    vendas_recentes = float(row['vendas_recentes'] or 0)
                    vendas_anteriores = float(row['vendas_anteriores'] or 0)
                    
                    # Calculate days active from registration date (dat_cadastro) to last sale or today
                    # This gives better metric for sold-out products
                    from datetime import date as date_class
                    today = date_class.today()
                    
                    # Use registration date if available, otherwise first sale date
                    start_date = dat_cadastro if dat_cadastro else primeira_venda
                    end_date = ultima_venda if ultima_venda else today
                    
                    if start_date and end_date:
                        days_active = max((end_date - start_date).days + 1, 1)
                    else:
                        days_active = 1
                    
                    # Calculate velocity (units per day)
                    # Products that sold out quickly should have high velocity
                    velocity = total_vendido / days_active if days_active > 0 else 0
                    
                    # Debug: log products with high sales
                    if total_vendido > 50 and len(performance_data) < 5:
                        logger.info(f"High sales product: {key}, total={total_vendido}, days={days_active}, velocity={velocity:.2f}")
                    
                    velocities.append(velocity)
                    
                    # Calculate trend (recent vs previous)
                    if vendas_anteriores > 0:
                        trend = vendas_recentes / vendas_anteriores
                    elif vendas_recentes > 0:
                        trend = 2.0  # Accelerating (recent sales but no previous)
                    else:
                        trend = 0.5  # Slowing down (no recent sales)
                    
                    performance_data[key] = {
                        "velocity": velocity,
                        "trend": trend,
                        "total_sold": total_vendido,
                        "days_active": days_active,
                        "dat_cadastro": start_date.strftime("%Y-%m-%d") if start_date else None,
                        "first_sale": primeira_venda.strftime("%Y-%m-%d") if primeira_venda else None,
                        "last_sale": ultima_venda.strftime("%Y-%m-%d") if ultima_venda else None,
                        "recent_sales": vendas_recentes,
                        "previous_sales": vendas_anteriores
                    }
                
                # Calculate percentiles for normalization
                velocities_sorted = sorted([v for v in velocities if v > 0])
                if velocities_sorted:
                    # Use percentiles for better distribution
                    n = len(velocities_sorted)
                    p25_idx = max(0, n // 4 - 1) if n >= 4 else 0
                    p50_idx = n // 2  # Median
                    p75_idx = min(n - 1, 3 * n // 4) if n >= 4 else n - 1
                    
                    p25 = velocities_sorted[p25_idx] if n >= 4 else velocities_sorted[0]
                    p50 = velocities_sorted[p50_idx]  # Median
                    p75 = velocities_sorted[p75_idx] if n >= 4 else velocities_sorted[-1]
                    max_velocity = velocities_sorted[-1]
                    min_velocity = velocities_sorted[0]
                    
                    logger.info(f"Velocity percentiles: p25={p25:.2f}, p50={p50:.2f}, p75={p75:.2f}, max={max_velocity:.2f}, min={min_velocity:.2f}, count={n}")
                else:
                    p25 = p50 = p75 = max_velocity = min_velocity = 1.0
                    logger.warning("No velocities found - using default baseline")
                
                # Normalize scores (0-100) using percentile-based scoring
                # This ensures better distribution: products at median get ~50, at 75th percentile get ~75, etc.
                for key, data in performance_data.items():
                    velocity = data['velocity']
                    trend = data['trend']
                    total_sold = data['total_sold']
                    
                    # Velocity score (0-70 points): based on percentiles
                    if velocity <= 0:
                        velocity_score = 0
                    elif velocity <= p25:
                        velocity_score = (velocity / p25) * 20 if p25 > 0 else 0  # 0-20 points
                    elif velocity <= p50:
                        velocity_score = 20 + ((velocity - p25) / (p50 - p25)) * 20 if (p50 - p25) > 0 else 40  # 20-40 points
                    elif velocity <= p75:
                        velocity_score = 40 + ((velocity - p50) / (p75 - p50)) * 20 if (p75 - p50) > 0 else 60  # 40-60 points
                    else:
                        # Above 75th percentile: scale to 70 points max
                        if max_velocity > p75:
                            velocity_score = 60 + min(((velocity - p75) / (max_velocity - p75)) * 10, 10)  # 60-70 points
                        else:
                            velocity_score = 70  # All above p75 get max
                    
                    # Trend score (0-30 points): recent performance
                    if trend >= 1.5:
                        trend_score = 30  # Accelerating strongly
                    elif trend >= 1.2:
                        trend_score = 25  # Accelerating
                    elif trend >= 1.0:
                        trend_score = 20  # Stable/improving
                    elif trend >= 0.8:
                        trend_score = 15  # Slightly slowing
                    elif trend >= 0.5:
                        trend_score = 10  # Slowing down
                    else:
                        trend_score = 5  # Slowing significantly
                    
                    # Combined score
                    score = velocity_score + trend_score
                    # Ensure it's 0-100
                    score = min(max(score, 0), 100)
                    
                    performance_data[key]['score'] = round(score, 1)
                    
                    # Debug logging for first few products
                    if len(performance_data) <= 5:
                        logger.info(f"Performance for {key}: velocity={velocity:.2f} (p50={p50:.2f}), trend={trend:.2f}, v_score={velocity_score:.1f}, t_score={trend_score:.1f}, final={score:.1f}, total_sold={total_sold}, days={data['days_active']}")
                
                logger.info(f"Calculated performance metrics for {len(performance_data)} products (year {ano_analise})")
                return performance_data
                
        except Exception as e:
            logger.error(f"Error calculating selling performance: {str(e)}", exc_info=True)
            return {}
