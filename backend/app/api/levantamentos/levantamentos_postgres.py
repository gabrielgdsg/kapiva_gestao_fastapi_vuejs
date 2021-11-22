from db_postgres.connection import CursorFromConnectionFromPool
from ..models.levantamentos import MarcaFornecedor


class LevantamentoPostgres:

    @classmethod
    def load_estoque_from_db(cls, dat_cadastro_ini, dat_cadastro_fim, cod_marca):
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''
            select pro.cod_grupo, gu.des_grupo, pro.cod_subgrupo, su.des_subgrupo,
        it.cod_produto, pro.des_produto, pro.cod_barra, pro.cod_referencia,
        sum(it.qtd_produto) as qtd, e.saldo_estoque,
        pro.vlr_custo_bruto, pro.vlr_custo_aquis, pro.vlr_venda1, sum(it.vlr_total) as total,
        pro.cod_grade, g.des_grade,
        pro.cod_tamanho, t.des_tamanho,
        pro.cod_cor, c.des_cor,
        cb.dat_cadastro,cb.dat_alteracao, cb.dat_emissao, cb.dat_lancamento, cb.dat_saida, cb.cod_fornece, 
        f.raz_fornece, f.fan_fornece,
        m.cod_marca, m.nom_marca,
        pfe.tipo_movto, pfe.qtd_movto, pfe.data as data_movto, pfe.cod_movto, pfe.cod_origem_movto
FROM PRODUTO pro
         LEFT OUTER JOIN MARCA m ON (m.COD_MARCA = pro.COD_MARCA)
         LEFT OUTER JOIN PRODUTO_ESTOQUE e ON (e.COD_EMPRESA = pro.COD_EMPRESA and
                                             e.COD_PRODUTO = pro.COD_PRODUTO)
        LEFT OUTER JOIN nfcompraitem it on (pro.cod_empresa = it.cod_empresa and pro.cod_produto = it.cod_produto)
        LEFT OUTER JOIN produto_ficha_estoq pfe on (pfe.cod_produto = it.cod_produto )
    LEFT OUTER JOIN grupo_produto gu on (gu.cod_grupo = pro.cod_grupo)
        LEFT OUTER JOIN nfcompra cb on (cb.cod_empresa = it.cod_empresa and cb.cod_interno = it.cod_interno)
        left outer join cores c on (c.cod_cor = pro.cod_cor)
         inner join grade_tamanho g on (g.cod_grade = pro.cod_grade)
         inner join tamanho t on (t.cod_grade = pro.cod_grade and t.cod_tamanho = pro.cod_tamanho)
         LEFT OUTER JOIN fornecedor f on (cb.cod_fornece = f.cod_fornece)
        LEFT OUTER JOIN subgrupo_produto su on (su.cod_grupo = pro.cod_grupo and su.cod_subgrupo = pro.cod_subgrupo)
where cb.cod_empresa = '1'
      and cb.dat_cadastro >= %s
      and cb.dat_cadastro < %s
      and (cb.flg_estorno is null or cb.flg_estorno = 'N')
      and m.cod_marca = %s
      and (pro.flg_mestre = 'N' or pro.flg_mestre is null)
group by pro.cod_grupo, gu.des_grupo, pro.cod_subgrupo, su.des_subgrupo,
             it.cod_produto, pro.des_produto,  pro.cod_barra, pro.cod_referencia,
             pro.vlr_custo_bruto, pro.vlr_custo_aquis, pro.vlr_venda1,
             pro.cod_grade, g.des_grade, e.saldo_estoque,
             pro.cod_tamanho, t.des_tamanho,
             pro.cod_cor,  c.des_cor,
             cb.dat_cadastro,cb.dat_alteracao, cb.dat_emissao, cb.dat_lancamento, cb.dat_saida, cb.cod_fornece,
             f.raz_fornece, f.fan_fornece,
             m.cod_marca, m.nom_marca,
             pfe.tipo_movto, pfe.qtd_movto, data_movto, pfe.cod_movto, pfe.cod_origem_movto
    order by 1, 2, 3, 4''', (dat_cadastro_ini, dat_cadastro_fim, cod_marca))
            dados_estoque = cursor.fetchall()
        return dados_estoque

    @classmethod
    def load_marcas_fornecedores_from_db(cls):
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(''' 
            select f.cod_fornece, f.raz_fornece, f.fan_fornece, m.cod_marca, m.nom_marca
            from produto p
            join fornecedor f on (p.cod_fornece = f.cod_fornece)
            join marca m on (p.cod_marca = m.cod_marca)
            group by m.cod_marca, f.cod_fornece
            ''')
            dados_marcas_fornecedores = cursor.fetchall()
            # marcas_for_class = marcas_fornecedores_to_class(dados_marcas_fornecedores)
        return dados_marcas_fornecedores

    # @classmethod
    # def marcas_fornecedores_to_class(cls, dados_marcas_fornecedores):
    #     marcas_fornecedores_list = []
    #     for i in range(len(dados_marcas_fornecedores)):
    #         print(dados_marcas_fornecedores)
    #         marca_fornecedor = MarcaFornecedor(
    #             cod_marca=dados_marcas_fornecedores[i][0], nom_marca=dados_marcas_fornecedores[i][1],
    #             cod_fornecedor=dados_marcas_fornecedores[i][2], raz_fornecedor=dados_marcas_fornecedores[i][3],
    #             fan_fornecedor=dados_marcas_fornecedores[i][4]
    #         )
    #         marcas_fornecedores_list.append(marca_fornecedor)
    #     return marcas_fornecedores_list

# and cb.cod_fornece = '936'


# class ComissaoPostgres:
#
#     @classmethod
#     def load_comissao_from_db(cls, dat_emissao_ini, dat_emissao_fim):
#         with CursorFromConnectionFromPool() as cursor:
#             cursor.execute('''SELECT cod_vendedor, nom_vendedor, sum(base_calculo) AS soma_base_calculo, sum(cred_dev) AS soma_cred_dev, sum(vlr_comissao) AS soma_vlr_comissao
#                         FROM (SELECT A.cod_vendedor,AB.nom_usuario AS nom_vendedor, sum(a.base_calc_comissao) AS base_calculo, sum(a.vlr_com_vendedor) AS vlr_comissao, sum(a.vlr_credito) AS cred_dev, A.dat_emissao
#                         FROM COMISSAO A
#                         LEFT OUTER JOIN USUARIOS AB ON	(A.cod_vendedor = AB.cod_usuario)
#                         WHERE A.dat_emissao >= %s AND A.dat_emissao <= %s
#                         GROUP BY cod_vendedor, nom_vendedor, dat_emissao) resultado_busca
#                         GROUP BY nom_vendedor, cod_vendedor
#                         ORDER BY soma_base_calculo DESC''', (dat_emissao_ini, dat_emissao_fim))
#             dados_comissao = cursor.fetchall()
#             return dados_comissao
