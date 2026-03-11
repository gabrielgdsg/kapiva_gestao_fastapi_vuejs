# from ..postgresdatabase import CursorFromConnectionFromPool
from app.db_postgres.connection import CursorFromConnectionFromPool
from decimal import Decimal


class CaixaPostgres:
    # def __init__(self,
    #              data_caixa,
    #              loj_suprimento,
    #              sist_troco,
    #              sist_pos,
    #              sist_dinheiro,
    #              loj_val_sangria):
    #     self.data_caixa = data_caixa
    #     self.loj_suprimento = loj_suprimento
    #     self.sist_troco = sist_troco
    #     self.sist_pos = sist_pos
    #     self.sist_dinheiro = sist_dinheiro
    #     self.loj_val_sangria = loj_val_sangria


    @classmethod
    def load_caixa_from_db(cls, data_caixa):
        print("load_caixa_from_db")
        print(data_caixa)
        with CursorFromConnectionFromPool() as cursor:
            # dados_sangria
            cursor.execute('''SELECT VALOR AS LOJ_SANGRIA 
                                FROM paf_caixa_item IT
                                LEFT JOIN PAF_CAIXA CX ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA
                                WHERE CX.DATA_CAIXA = %s AND meio_pagto =3''', (data_caixa,))
            dados_sangria = cursor.fetchall()
            # dados_suprimento
            cursor.execute('''SELECT SUM(VALOR)-.02 AS LOJ_SUPRIMENTO FROM paf_caixa_item IT
                            LEFT JOIN PAF_CAIXA CX ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA
                            WHERE CX.DATA_CAIXA = %s AND meio_pagto =2''', (data_caixa,))
            dados_suprimento = cursor.fetchall()
            # dados_troco
            cursor.execute('''SELECT 
                        SUM(CASE
                            WHEN IT.TIPO_MOVTO = 'S' THEN IT.VALOR * (- 1)
                            ELSE IT.VALOR
                            END) SIST_TROCO
                        FROM PAF_CAIXA CX
                        LEFT JOIN PAF_CAIXA_ITEM IT
                               ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA AND IT.MEIO_PAGTO NOT IN (2, 3)
                        WHERE CX.DATA_CAIXA = %s AND IT.MODALIDADE = 0''', (data_caixa,))
            dados_troco = cursor.fetchall()
            # dados_pos
            cursor.execute('''SELECT 
                        SUM(CASE
                            WHEN IT.TIPO_MOVTO = 'S' THEN IT.VALOR * (- 1)
                            ELSE IT.VALOR
                            END) SIST_POS
                        FROM PAF_CAIXA CX
                        LEFT JOIN PAF_CAIXA_ITEM IT
                               ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA AND IT.MEIO_PAGTO NOT IN (2, 3)
                        WHERE CX.DATA_CAIXA = %s  AND IT.MODALIDADE = 13''', (data_caixa,))
            dados_pos = cursor.fetchall()
            # dados_dinheiro
            cursor.execute('''SELECT 
                        SUM(CASE
                            WHEN IT.TIPO_MOVTO = 'S' THEN IT.VALOR * (- 1)
                            ELSE IT.VALOR
                            END) SIST_DIN
                        FROM PAF_CAIXA CX
                        LEFT JOIN PAF_CAIXA_ITEM IT
                               ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA AND IT.MEIO_PAGTO NOT IN (2, 3)
                        WHERE CX.DATA_CAIXA = %s AND IT.MODALIDADE = 1''', (data_caixa,))
            dados_dinheiro = cursor.fetchall()
            loj_sangria = [i[0] or [] for i in dados_sangria]
            loj_suprimento = [i[0] or 0 for i in dados_suprimento]
            sist_troco = [i[0] or 0 for i in dados_troco]
            sist_pos = [i[0] or 0 for i in dados_pos]
            sist_dinheiro = [i[0] or 0 for i in dados_dinheiro]
            # dados_caixa = {loj_sangria, loj_suprimento, sist_troco, sist_pos, sist_dinheiro}

            return loj_sangria, loj_suprimento, sist_troco, sist_pos, sist_dinheiro
            # return dados_caixa

    @classmethod
    def _get_caixa_operador_map(cls, cursor, data_caixa):
        """Try to get COD_CAIXA -> operador name. Returns dict; empty if not available."""
        queries = [
            # PAF_CAIXA.COD_OPERADOR -> OPERADOR
            '''SELECT CX.COD_CAIXA, COALESCE(O.NOM_OPERADOR, O.NOM_OPER, '') 
               FROM PAF_CAIXA CX 
               LEFT JOIN OPERADOR O ON O.COD_OPERADOR = CX.COD_OPERADOR 
               WHERE CX.DATA_CAIXA = %s''',
            # PAF_CAIXA.COD_OPERADOR -> USUARIOS
            '''SELECT CX.COD_CAIXA, COALESCE(U.NOM_USUARIO, U.NOM_USER, '') 
               FROM PAF_CAIXA CX 
               LEFT JOIN USUARIOS U ON U.COD_USUARIO = CX.COD_OPERADOR 
               WHERE CX.DATA_CAIXA = %s''',
            # PAF_CAIXA.COD_USUARIO -> USUARIOS (alguns PAF usam cod_usuario)
            '''SELECT CX.COD_CAIXA, COALESCE(U.NOM_USUARIO, U.NOM_USER, '') 
               FROM PAF_CAIXA CX 
               LEFT JOIN USUARIOS U ON U.COD_USUARIO = CX.COD_USUARIO 
               WHERE CX.DATA_CAIXA = %s''',
            # COD_CAIXA = cod_usuario (em alguns sistemas o caixa é o usuário)
            '''SELECT CX.COD_CAIXA, COALESCE(U.NOM_USUARIO, U.NOM_USER, '') 
               FROM PAF_CAIXA CX 
               LEFT JOIN USUARIOS U ON U.COD_USUARIO = CX.COD_CAIXA 
               WHERE CX.DATA_CAIXA = %s''',
            # PAF_CAIXA com coluna NOM_OPERADOR ou DES_CAIXA direta
            '''SELECT COD_CAIXA, COALESCE(NOM_OPERADOR, DES_CAIXA, DESCRICAO, '') 
               FROM PAF_CAIXA WHERE DATA_CAIXA = %s''',
        ]
        for q in queries:
            try:
                cursor.execute(q, (data_caixa,))
                out = {}
                for r in cursor.fetchall():
                    if r[0] is not None:
                        nom = (r[1] or '').strip()
                        out[r[0]] = nom if nom else None
                if out:
                    return out
            except Exception:
                try:
                    cursor.connection.rollback()
                except Exception:
                    pass
                continue
        return {}

    @classmethod
    def load_caixas_from_db(cls, data_caixa):
        """
        Load caixa data per COD_CAIXA for a given date.
        Returns list of dicts, one per caixa: [{cod_caixa, nom_operador?, loj_sangria, ...}, ...]
        """
        with CursorFromConnectionFromPool() as cursor:
            operador_map = cls._get_caixa_operador_map(cursor, data_caixa)
            # Get distinct COD_CAIXA for the date
            cursor.execute(
                '''SELECT DISTINCT COD_CAIXA FROM PAF_CAIXA WHERE DATA_CAIXA = %s ORDER BY COD_CAIXA''',
                (data_caixa,)
            )
            cod_caixas = [r[0] for r in cursor.fetchall() if r[0] is not None]
            if not cod_caixas:
                return []

            result = []
            for cod_caixa in cod_caixas:
                # Sangria (per caixa)
                cursor.execute('''
                    SELECT VALOR AS LOJ_SANGRIA FROM paf_caixa_item IT
                    LEFT JOIN PAF_CAIXA CX ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA
                    WHERE CX.DATA_CAIXA = %s AND CX.COD_CAIXA = %s AND meio_pagto = 3
                ''', (data_caixa, cod_caixa))
                loj_sangria = [Decimal(str(i[0] or 0)) for i in cursor.fetchall()]

                # Suprimento (per caixa)
                cursor.execute('''
                    SELECT COALESCE(SUM(VALOR), 0) - 0.02 AS LOJ_SUPRIMENTO FROM paf_caixa_item IT
                    LEFT JOIN PAF_CAIXA CX ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA
                    WHERE CX.DATA_CAIXA = %s AND CX.COD_CAIXA = %s AND meio_pagto = 2
                ''', (data_caixa, cod_caixa))
                row = cursor.fetchone()
                loj_suprimento = Decimal(str(row[0])) if row and row[0] is not None else Decimal('0')

                # Troco (per caixa) - use COALESCE for NULL from LEFT JOIN
                cursor.execute('''
                    SELECT COALESCE(SUM(CASE WHEN IT.TIPO_MOVTO = 'S' THEN IT.VALOR * (-1) ELSE IT.VALOR END), 0) AS SIST_TROCO
                    FROM PAF_CAIXA CX
                    LEFT JOIN PAF_CAIXA_ITEM IT ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA AND IT.MEIO_PAGTO NOT IN (2, 3) AND IT.MODALIDADE = 0
                    WHERE CX.DATA_CAIXA = %s AND CX.COD_CAIXA = %s
                ''', (data_caixa, cod_caixa))
                row = cursor.fetchone()
                sist_troco = Decimal(str(row[0])) if row and row[0] is not None else Decimal('0')

                # POS (per caixa)
                cursor.execute('''
                    SELECT COALESCE(SUM(CASE WHEN IT.TIPO_MOVTO = 'S' THEN IT.VALOR * (-1) ELSE IT.VALOR END), 0) AS SIST_POS
                    FROM PAF_CAIXA CX
                    LEFT JOIN PAF_CAIXA_ITEM IT ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA AND IT.MEIO_PAGTO NOT IN (2, 3) AND IT.MODALIDADE = 13
                    WHERE CX.DATA_CAIXA = %s AND CX.COD_CAIXA = %s
                ''', (data_caixa, cod_caixa))
                row = cursor.fetchone()
                sist_pos = Decimal(str(row[0])) if row and row[0] is not None else Decimal('0')

                # Dinheiro (per caixa)
                cursor.execute('''
                    SELECT COALESCE(SUM(CASE WHEN IT.TIPO_MOVTO = 'S' THEN IT.VALOR * (-1) ELSE IT.VALOR END), 0) AS SIST_DIN
                    FROM PAF_CAIXA CX
                    LEFT JOIN PAF_CAIXA_ITEM IT ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA AND IT.MEIO_PAGTO NOT IN (2, 3) AND IT.MODALIDADE = 1
                    WHERE CX.DATA_CAIXA = %s AND CX.COD_CAIXA = %s
                ''', (data_caixa, cod_caixa))
                row = cursor.fetchone()
                sist_dinheiro = Decimal(str(row[0])) if row and row[0] is not None else Decimal('0')

                result.append({
                    'cod_caixa': cod_caixa,
                    'nom_operador': operador_map.get(cod_caixa),
                    'loj_sangria': loj_sangria,
                    'loj_suprimento': loj_suprimento,
                    'sist_troco': sist_troco,
                    'sist_pos': sist_pos,
                    'sist_dinheiro': sist_dinheiro,
                })
            return result


# class SangriaPostgres:
#     def __init__(self,
#                  loj_sangria):
#         self.loj_sangria = loj_sangria
#
#     @classmethod
#     def load_sangria_from_db(cls, data_caixa):
#         with CursorFromConnectionFromPool() as cursor:
#             # dados_sangria
#             cursor.execute('''SELECT VALOR AS LOJ_SANGRIA
#                                 FROM paf_caixa_item IT
#                                 LEFT JOIN PAF_CAIXA CX ON IT.COD_EMPRESA = CX.COD_EMPRESA AND IT.COD_CAIXA = CX.COD_CAIXA
#                                 WHERE CX.DATA_CAIXA = %s AND meio_pagto =3''', (data_caixa,))
#             dados_sangria = cursor.fetchall()
#             loj_sangria = [i[0] or [] for i in dados_sangria]
#             return cls(loj_sangria)