# from ..postgresdatabase import CursorFromConnectionFromPool
from db_postgres.connection import CursorFromConnectionFromPool


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