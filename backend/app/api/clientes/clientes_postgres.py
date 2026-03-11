from app.db_postgres.connection import CursorFromConnectionFromPool
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ClientesPostgres:
    """
    Queries for the Clientes dashboard.
    Tables: cliente, receber, nota_fiscal, cidade
    """

    @classmethod
    def get_clientes_lista(
        cls,
        search: Optional[str] = None,
        apenas_ativos: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict]:
        try:
            params = []
            where_clauses = ["cl.cod_empresa = 1"]
            if apenas_ativos:
                where_clauses.append("(cl.flg_ativo IS NULL OR cl.flg_ativo = 'S')")
            if search:
                where_clauses.append(
                    "(LOWER(COALESCE(cl.fan_cliente, cl.raz_cliente, '')) LIKE LOWER(%s)"
                    " OR cl.num_celular LIKE %s OR cl.num_fone LIKE %s)"
                )
                like = f"%{search}%"
                params += [like, like, like]
            where_sql = " AND ".join(where_clauses)
            query = f"""
                SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                    COALESCE(cl.num_celular, cl.num_fone, '') AS telefone, COALESCE(ci.nom_cidade, '') AS cidade,
                    cl.dat_nascto, cl.dat_ultima_compra, cl.dat_cadastro, COALESCE(cl.vlr_limite, 0) AS vlr_limite,
                    cl.flg_ativo, cl.flg_bloq_contas_vencidas, cl.flg_bloq_limite_ultrapassado,
                    COALESCE(nf_stats.total_gasto, 0) AS total_gasto, COALESCE(nf_stats.total_compras, 0) AS total_compras,
                    COALESCE(nf_stats.ticket_medio, 0) AS ticket_medio, COALESCE(nf_stats.ultima_compra_nf, NULL) AS ultima_compra_nf,
                    COALESCE(rec_stats.vlr_aberto, 0) AS vlr_aberto, COALESCE(rec_stats.vlr_vencido, 0) AS vlr_vencido,
                    COALESCE(rec_stats.parcelas_abertas, 0) AS parcelas_abertas, COALESCE(rec_stats.parcelas_vencidas, 0) AS parcelas_vencidas,
                    COALESCE(rec_stats.juros_recebidos, 0) AS juros_recebidos,
                    COALESCE(rec_stats.dat_vencto_mais_antiga, NULL) AS dat_vencto_mais_antiga
                FROM cliente cl
                LEFT JOIN cidade ci ON ci.cod_cidade = cl.cod_cidade
                LEFT JOIN LATERAL (
                    SELECT SUM(nf.vlr_total) AS total_gasto, COUNT(DISTINCT nf.nf_interno) AS total_compras,
                        CASE WHEN COUNT(DISTINCT nf.nf_interno) > 0 THEN SUM(nf.vlr_total)/COUNT(DISTINCT nf.nf_interno) ELSE 0 END AS ticket_medio,
                        MAX(nf.dat_emissao::date) AS ultima_compra_nf
                    FROM nota_fiscal nf WHERE nf.cod_cliente = cl.cod_cliente
                        AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                        AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                ) nf_stats ON true
                LEFT JOIN LATERAL (
                    SELECT SUM(CASE WHEN r.flg_aberto = 'S' THEN r.vlr_saldo ELSE 0 END) AS vlr_aberto,
                        SUM(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END) AS vlr_vencido,
                        COUNT(CASE WHEN r.flg_aberto = 'S' THEN 1 END) AS parcelas_abertas,
                        COUNT(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN 1 END) AS parcelas_vencidas,
                        SUM(COALESCE(r.vlr_juros, 0)) AS juros_recebidos,
                        MIN(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN r.dat_vencto END) AS dat_vencto_mais_antiga
                    FROM receber r WHERE r.cod_cliente = cl.cod_cliente AND r.cod_empresa = 1
                ) rec_stats ON true
                WHERE """ + where_sql + """
                ORDER BY cl.dat_ultima_compra DESC NULLS LAST, nom_cliente
                LIMIT %s OFFSET %s
            """
            params += [limit, offset]
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(query, params)
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_clientes_lista: {e}", exc_info=True)
            raise

    @classmethod
    def get_cliente_detalhe(cls, cod_cliente: int) -> Optional[Dict]:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                        COALESCE(cl.num_celular, cl.num_fone, '') AS telefone, cl.email, COALESCE(ci.nom_cidade, '') AS cidade,
                        cl.cod_estado, cl.dat_nascto, cl.dat_ultima_compra, cl.dat_cadastro, COALESCE(cl.vlr_limite, 0) AS vlr_limite,
                        cl.flg_ativo, cl.flg_bloq_contas_vencidas, cl.flg_juros, cl.observacao, cl.cpf_cgc, cl.nom_profissao, cl.vlr_renda
                    FROM cliente cl LEFT JOIN cidade ci ON ci.cod_cidade = cl.cod_cidade
                    WHERE cl.cod_cliente = %s AND cl.cod_empresa = 1
                """, (cod_cliente,))
                row = cursor.fetchone()
                if not row:
                    return None
                return dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            logger.error(f"Error in get_cliente_detalhe {cod_cliente}: {e}", exc_info=True)
            raise

    @classmethod
    def get_cliente_receber(cls, cod_cliente: int, apenas_aberto: bool = False) -> List[Dict]:
        try:
            where_extra = "AND r.flg_aberto = 'S'" if apenas_aberto else ""
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(f"""
                    SELECT r.cod_receber, r.num_doc, r.qtd_parcelas AS parcela_label, r.dat_emissao, r.dat_vencto, r.dat_ultpagto,
                        r.vlr_doc, r.vlr_pago, r.vlr_saldo, COALESCE(r.vlr_juros, 0) AS vlr_juros, COALESCE(r.vlr_descto, 0) AS vlr_descto,
                        r.flg_aberto, r.prc_finan_venda,
                        CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN (CURRENT_DATE - r.dat_vencto)::integer
                             WHEN r.flg_aberto != 'S' AND r.dat_ultpagto IS NOT NULL AND r.dat_ultpagto > r.dat_vencto
                             THEN (r.dat_ultpagto - r.dat_vencto)::integer ELSE 0 END AS dias_atraso,
                        r.orig_doc, r.cod_orig_doc
                    FROM receber r WHERE r.cod_cliente = %s AND r.cod_empresa = 1 {where_extra}
                    ORDER BY r.dat_vencto DESC
                """, (cod_cliente,))
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_cliente_receber {cod_cliente}: {e}", exc_info=True)
            raise

    @classmethod
    def get_cliente_compras(cls, cod_cliente: int, limit: int = 50) -> List[Dict]:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT nf.nf_interno, nf.numero AS num_nf, nf.dat_emissao::date AS dat_emissao, nf.vlr_total,
                        nf.prazomedio AS prazo_medio_dias, COALESCE(u.nom_usuario, '') AS nom_vendedor
                    FROM nota_fiscal nf LEFT JOIN usuarios u ON u.cod_usuario = nf.cod_usuario
                    WHERE nf.cod_cliente = %s AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                        AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                    ORDER BY nf.dat_emissao DESC LIMIT %s
                """, (cod_cliente, limit))
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_cliente_compras {cod_cliente}: {e}", exc_info=True)
            raise

    @classmethod
    def get_kpis_gerais(cls) -> Dict:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT COUNT(DISTINCT cl.cod_cliente) AS total_clientes_ativos,
                        COUNT(DISTINCT CASE WHEN rec.vlr_aberto > 0 THEN cl.cod_cliente END) AS clientes_com_divida,
                        COUNT(DISTINCT CASE WHEN rec.vlr_vencido > 0 THEN cl.cod_cliente END) AS clientes_inadimplentes,
                        COALESCE(SUM(rec.vlr_aberto), 0) AS total_em_aberto, COALESCE(SUM(rec.vlr_vencido), 0) AS total_vencido,
                        COALESCE(SUM(rec.juros_recebidos), 0) AS total_juros_recebidos,
                        COUNT(DISTINCT cl.cod_cliente) FILTER (WHERE cl.flg_ativo = 'S' OR cl.flg_ativo IS NULL) AS clientes_ativos_count
                    FROM cliente cl
                    LEFT JOIN LATERAL (
                        SELECT SUM(CASE WHEN r.flg_aberto = 'S' THEN r.vlr_saldo ELSE 0 END) AS vlr_aberto,
                            SUM(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END) AS vlr_vencido,
                            SUM(COALESCE(r.vlr_juros, 0)) AS juros_recebidos
                        FROM receber r WHERE r.cod_cliente = cl.cod_cliente AND r.cod_empresa = 1
                    ) rec ON true
                    WHERE cl.cod_empresa = 1
                """)
                row = cursor.fetchone()
                return dict(zip([d[0] for d in cursor.description], row))
        except Exception as e:
            logger.error(f"Error in get_kpis_gerais: {e}", exc_info=True)
            raise

    @classmethod
    def get_inadimplencia_historico(cls, meses: int = 15) -> List[Dict]:
        """Returns past months only (excludes future). vlr_vencido = raw overdue (no interest)."""
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT TO_CHAR(DATE_TRUNC('month', r.dat_vencto), 'Mon/YY') AS period,
                        DATE_TRUNC('month', r.dat_vencto)::date AS period_date,
                        SUM(r.vlr_doc) AS vlr_emitido, SUM(r.vlr_pago) AS vlr_pago,
                        SUM(CASE WHEN r.flg_aberto = 'S' THEN r.vlr_saldo ELSE 0 END) AS vlr_aberto,
                        SUM(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END) AS vlr_vencido,
                        COUNT(*) AS total_parcelas,
                        COUNT(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN 1 END) AS parcelas_vencidas,
                        SUM(COALESCE(r.vlr_juros, 0)) AS vlr_juros,
                        CASE WHEN SUM(r.vlr_doc) > 0 THEN ROUND(
                            SUM(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END)
                            / SUM(r.vlr_doc) * 100, 2) ELSE 0 END AS taxa
                    FROM receber r
                    WHERE r.cod_empresa = 1
                        AND r.dat_vencto >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month' * %s)
                        AND DATE_TRUNC('month', r.dat_vencto) <= DATE_TRUNC('month', CURRENT_DATE)
                    GROUP BY DATE_TRUNC('month', r.dat_vencto) ORDER BY period_date ASC
                """, (meses,))
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                out = []
                for row in rows:
                    d = dict(zip(cols, row))
                    d["taxa_inadimplencia"] = float(d.get("taxa", 0) or 0)
                    d["vlr_vencido"] = float(d.get("vlr_vencido", 0) or 0)
                    if d.get("period_date"):
                        d["period_ym"] = str(d["period_date"])[:7]
                    out.append(d)
                return out
        except Exception as e:
            logger.error(f"Error in get_inadimplencia_historico: {e}", exc_info=True)
            raise

    @classmethod
    def get_devedores_por_periodo(cls, period: str, limit: int = 50) -> List[Dict]:
        """Clients with overdue in period (YYYY-MM). Ordered by vlr_vencido desc."""
        try:
            parts = period.split("-")
            if len(parts) != 2:
                return []
            year, month = int(parts[0]), int(parts[1])
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                        COALESCE(cl.num_celular, cl.num_fone, '') AS telefone,
                        SUM(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END) AS vlr_vencido,
                        MIN(r.dat_vencto) AS dat_vencto_mais_antiga,
                        (CURRENT_DATE - MIN(r.dat_vencto))::integer AS dias_em_atraso,
                        COUNT(*) AS parcelas_abertas
                    FROM receber r JOIN cliente cl ON cl.cod_cliente = r.cod_cliente AND cl.cod_empresa = r.cod_empresa
                    WHERE r.cod_empresa = 1 AND r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE
                        AND r.dat_vencto >= %s::date
                        AND r.dat_vencto < %s::date + INTERVAL '1 month'
                    GROUP BY cl.cod_cliente, cl.fan_cliente, cl.raz_cliente, cl.num_celular, cl.num_fone
                    HAVING SUM(CASE WHEN r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END) > 0
                    ORDER BY vlr_vencido DESC LIMIT %s
                """, (f"{year}-{month:02d}-01", f"{year}-{month:02d}-01", limit))
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_devedores_por_periodo: {e}", exc_info=True)
            raise

    @classmethod
    def get_top_devedores(cls, limit: int = 10) -> List[Dict]:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                        COALESCE(cl.num_celular, cl.num_fone, '') AS telefone,
                        SUM(r.vlr_saldo) AS vlr_total_aberto,
                        SUM(CASE WHEN r.dat_vencto < CURRENT_DATE THEN r.vlr_saldo ELSE 0 END) AS vlr_vencido,
                        MIN(r.dat_vencto) AS dat_vencto_mais_antiga,
                        (CURRENT_DATE - MIN(r.dat_vencto))::integer AS dias_em_atraso,
                        COUNT(*) AS parcelas_abertas
                    FROM receber r JOIN cliente cl ON cl.cod_cliente = r.cod_cliente AND cl.cod_empresa = r.cod_empresa
                    WHERE r.cod_empresa = 1 AND r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE
                    GROUP BY cl.cod_cliente, cl.fan_cliente, cl.raz_cliente, cl.num_celular, cl.num_fone
                    ORDER BY vlr_vencido DESC LIMIT %s
                """, (limit,))
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_top_devedores: {e}", exc_info=True)
            raise

    @classmethod
    def get_distribuicao_parcelas(cls, meses: int = 12) -> List[Dict]:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT CASE WHEN r.qtd_parcelas ~ '^[0-9]+/[0-9]+$' THEN SPLIT_PART(r.qtd_parcelas, '/', 2)::integer ELSE 1 END AS total_parcelas,
                        COUNT(DISTINCT r.num_doc) AS total_vendas, SUM(r.vlr_doc) AS vlr_total
                    FROM receber r
                    WHERE r.cod_empresa = 1 AND r.dat_emissao >= CURRENT_DATE - INTERVAL '1 month' * %s
                    GROUP BY total_parcelas ORDER BY total_parcelas
                """, (meses,))
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                out = []
                total = sum(r[1] for r in rows) or 1
                for row in rows:
                    d = dict(zip(cols, row))
                    d["label"] = f"{int(d['total_parcelas'])}x"
                    d["count"] = int(d.get("total_vendas", 0))
                    d["pct"] = round(int(d.get("total_vendas", 0)) / total * 100)
                    out.append(d)
                return out
        except Exception as e:
            logger.error(f"Error in get_distribuicao_parcelas: {e}", exc_info=True)
            raise

    @classmethod
    def get_aniversariantes_mes(cls, mes: Optional[int] = None) -> List[Dict]:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                        COALESCE(cl.num_celular, cl.num_fone, '') AS telefone, cl.dat_nascto,
                        EXTRACT(DAY FROM cl.dat_nascto)::integer AS dia_nascto, COALESCE(ci.nom_cidade, '') AS cidade,
                        cl.dat_ultima_compra, COALESCE(rec.vlr_aberto, 0) AS vlr_aberto
                    FROM cliente cl LEFT JOIN cidade ci ON ci.cod_cidade = cl.cod_cidade
                    LEFT JOIN LATERAL (SELECT SUM(CASE WHEN r.flg_aberto = 'S' THEN r.vlr_saldo ELSE 0 END) AS vlr_aberto
                        FROM receber r WHERE r.cod_cliente = cl.cod_cliente AND r.cod_empresa = 1) rec ON true
                    WHERE cl.cod_empresa = 1 AND cl.dat_nascto IS NOT NULL
                        AND EXTRACT(MONTH FROM cl.dat_nascto) = COALESCE(%s, EXTRACT(MONTH FROM CURRENT_DATE))
                        AND (cl.flg_ativo IS NULL OR cl.flg_ativo = 'S')
                    ORDER BY EXTRACT(DAY FROM cl.dat_nascto)
                """, (mes,))
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_aniversariantes_mes: {e}", exc_info=True)
            raise

    @classmethod
    def get_clientes_vip(cls, limit: int = 20, range_type: str = "all") -> List[Dict]:
        """range_type: all, this_year, last_year, last_2_years"""
        nf_filter = ""
        if range_type == "this_year":
            nf_filter = " AND nf.dat_emissao::date >= DATE_TRUNC('year', CURRENT_DATE)::date"
        elif range_type == "last_year":
            nf_filter = " AND nf.dat_emissao::date >= DATE_TRUNC('year', CURRENT_DATE)::date - INTERVAL '1 year' AND nf.dat_emissao::date < DATE_TRUNC('year', CURRENT_DATE)::date"
        elif range_type == "last_2_years":
            nf_filter = " AND nf.dat_emissao::date >= CURRENT_DATE - INTERVAL '2 years'"
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(f"""
                    SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                        COALESCE(cl.num_celular, cl.num_fone, '') AS telefone, COALESCE(ci.nom_cidade, '') AS cidade,
                        cl.dat_ultima_compra, cl.dat_cadastro, nf_stats.total_gasto AS ltv, nf_stats.total_compras,
                        nf_stats.ticket_medio, nf_stats.primeira_compra, COALESCE(rec.vlr_aberto, 0) AS vlr_aberto,
                        COALESCE(rec.juros_pagos, 0) AS juros_pagos
                    FROM cliente cl LEFT JOIN cidade ci ON ci.cod_cidade = cl.cod_cidade
                    JOIN LATERAL (
                        SELECT SUM(nf.vlr_total) AS total_gasto, COUNT(DISTINCT nf.nf_interno) AS total_compras,
                            SUM(nf.vlr_total)/COUNT(DISTINCT nf.nf_interno) AS ticket_medio,
                            MIN(nf.dat_emissao::date) AS primeira_compra
                        FROM nota_fiscal nf WHERE nf.cod_cliente = cl.cod_cliente
                            AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
                            AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
                            {nf_filter}
                        HAVING COUNT(DISTINCT nf.nf_interno) > 0
                    ) nf_stats ON true
                    LEFT JOIN LATERAL (
                        SELECT SUM(CASE WHEN r.flg_aberto = 'S' THEN r.vlr_saldo ELSE 0 END) AS vlr_aberto,
                            SUM(COALESCE(r.vlr_juros, 0)) AS juros_pagos
                        FROM receber r WHERE r.cod_cliente = cl.cod_cliente AND r.cod_empresa = 1
                    ) rec ON true
                    WHERE cl.cod_empresa = 1 AND (cl.flg_ativo IS NULL OR cl.flg_ativo = 'S')
                    ORDER BY nf_stats.total_gasto DESC LIMIT %s
                """, (limit,))
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_clientes_vip: {e}", exc_info=True)
            raise

    @classmethod
    def get_writeoffs_postgres(cls) -> Dict:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT COUNT(DISTINCT r.cod_cliente) AS total_clientes_perdidos, SUM(r.vlr_saldo) AS total_perdido,
                        SUM(COALESCE(r.vlr_juros, 0)) AS total_juros_perdidos
                    FROM receber r WHERE r.cod_empresa = 1 AND r.flg_aberto = 'S'
                        AND r.dat_vencto < CURRENT_DATE - INTERVAL '365 days'
                        AND NOT EXISTS (SELECT 1 FROM receber r2 WHERE r2.cod_cliente = r.cod_cliente AND r2.cod_empresa = 1 AND COALESCE(r2.vlr_pago, 0) > 0)
                """)
                row = cursor.fetchone()
                summary = dict(zip([d[0] for d in cursor.description], row))
                cursor.execute("SELECT COALESCE(SUM(vlr_juros), 0) AS total_juros_recebidos_geral FROM receber WHERE cod_empresa = 1 AND COALESCE(vlr_juros, 0) > 0")
                r2 = cursor.fetchone()
                summary["total_juros_recebidos_geral"] = float(r2[0]) if r2 else 0.0
                return summary
        except Exception as e:
            logger.error(f"Error in get_writeoffs_postgres: {e}", exc_info=True)
            raise

    @classmethod
    def get_writeoff_clientes(cls) -> List[Dict]:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT cl.cod_cliente, COALESCE(cl.fan_cliente, cl.raz_cliente, '') AS nom_cliente,
                        COALESCE(cl.num_celular, cl.num_fone, '') AS telefone, SUM(r.vlr_saldo) AS vlr_perdido,
                        SUM(COALESCE(r.vlr_juros, 0)) AS juros_perdidos, MIN(r.dat_vencto) AS dat_vencto_mais_antiga,
                        COUNT(*) AS parcelas_perdidas
                    FROM receber r JOIN cliente cl ON cl.cod_cliente = r.cod_cliente AND cl.cod_empresa = r.cod_empresa
                    WHERE r.cod_empresa = 1 AND r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE - INTERVAL '365 days'
                        AND NOT EXISTS (SELECT 1 FROM receber r2 WHERE r2.cod_cliente = r.cod_cliente AND r2.cod_empresa = 1 AND COALESCE(r2.vlr_pago, 0) > 0)
                    GROUP BY cl.cod_cliente, cl.fan_cliente, cl.raz_cliente, cl.num_celular, cl.num_fone
                    ORDER BY vlr_perdido DESC
                """)
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_writeoff_clientes: {e}", exc_info=True)
            raise

    @classmethod
    def get_cliente_score_data(cls, cod_cliente: int) -> Dict:
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS total_parcelas,
                        COUNT(CASE WHEN r.flg_aberto != 'S' THEN 1 END) AS parcelas_pagas,
                        COUNT(CASE WHEN r.flg_aberto != 'S' AND r.dat_ultpagto > r.dat_vencto THEN 1 END) AS pagas_com_atraso,
                        COUNT(CASE WHEN r.flg_aberto = 'S' AND r.dat_vencto < CURRENT_DATE THEN 1 END) AS parcelas_vencidas,
                        SUM(COALESCE(r.vlr_juros, 0)) AS total_juros_pagos,
                        SUM(CASE WHEN r.flg_aberto = 'S' THEN r.vlr_saldo ELSE 0 END) AS saldo_em_aberto,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CASE WHEN r.flg_aberto != 'S' AND r.dat_ultpagto IS NOT NULL AND r.dat_ultpagto > r.dat_vencto
                            THEN (r.dat_ultpagto - r.dat_vencto)::integer ELSE 0 END) AS mediana_dias_atraso,
                        MAX(CASE WHEN r.flg_aberto != 'S' THEN r.dat_ultpagto END) AS ultima_quitacao
                    FROM receber r WHERE r.cod_cliente = %s AND r.cod_empresa = 1
                """, (cod_cliente,))
                row = cursor.fetchone()
                if not row:
                    return {}
                data = dict(zip([d[0] for d in cursor.description], row))
                if data.get("ultima_quitacao"):
                    cursor.execute("""
                        SELECT COUNT(*) FROM nota_fiscal WHERE cod_cliente = %s AND dat_emissao::date > %s
                            AND (flg_cancelado IS NULL OR flg_cancelado != 'S')
                            AND (cod_grupo_operacoes IS NULL OR cod_grupo_operacoes != 6)
                    """, (cod_cliente, data["ultima_quitacao"]))
                    data["recompra_pos_quita"] = cursor.fetchone()[0] > 0
                else:
                    data["recompra_pos_quita"] = False
                return data
        except Exception as e:
            logger.error(f"Error in get_cliente_score_data {cod_cliente}: {e}", exc_info=True)
            raise
