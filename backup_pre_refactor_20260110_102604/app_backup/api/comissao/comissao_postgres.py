from db_postgres.connection import CursorFromConnectionFromPool


class ComissaoPostgres:

    @classmethod
    def load_comissao_from_db(cls, dat_emissao_ini, dat_emissao_fim):
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''SELECT cod_vendedor, nom_vendedor, sum(base_calculo) AS soma_base_calculo, sum(cred_dev) AS soma_cred_dev, sum(vlr_comissao) AS soma_vlr_comissao
                        FROM (SELECT A.cod_vendedor,AB.nom_usuario AS nom_vendedor, sum(a.base_calc_comissao) AS base_calculo, sum(a.vlr_com_vendedor) AS vlr_comissao, sum(a.vlr_credito) AS cred_dev, A.dat_emissao
                        FROM COMISSAO A
                        LEFT OUTER JOIN USUARIOS AB ON	(A.cod_vendedor = AB.cod_usuario)
                        WHERE A.dat_emissao >= %s AND A.dat_emissao <= %s
                        GROUP BY cod_vendedor, nom_vendedor, dat_emissao) resultado_busca
                        GROUP BY nom_vendedor, cod_vendedor    
                        ORDER BY soma_base_calculo DESC''', (dat_emissao_ini, dat_emissao_fim))
            dados_comissao = cursor.fetchall()
            return dados_comissao



