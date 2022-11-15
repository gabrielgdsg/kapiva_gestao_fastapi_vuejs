from db_postgres.connection import CursorFromConnectionFromPool

class EstoquePostgres:

    @classmethod
    def load_estoque_produtos_from_db(cls, data_movto_ini):
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''
                select pro.cod_grupo, gu.des_grupo, pro.cod_subgrupo, su.des_subgrupo,
            pro.cod_produto, pro.des_produto, pro.cod_barra, pro.cod_referencia,
            sum(it.qtd_produto) as qtd, e.saldo_estoque,
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
             LEFT OUTER JOIN PRODUTO_ESTOQUE e ON (e.COD_EMPRESA = pro.COD_EMPRESA and
                                                 e.COD_PRODUTO = pro.COD_PRODUTO)
            LEFT OUTER JOIN nfcompraitem it on (pro.cod_empresa = it.cod_empresa and pro.cod_produto = it.cod_produto)
            LEFT OUTER JOIN produto_ficha_estoq pfe on (pfe.cod_produto = pro.cod_produto )
        LEFT OUTER JOIN grupo_produto gu on (gu.cod_grupo = pro.cod_grupo)
            LEFT OUTER JOIN nfcompra cb on (cb.cod_empresa = it.cod_empresa and cb.cod_interno = it.cod_interno)
            left outer join cores c on (c.cod_cor = pro.cod_cor)
             inner join grade_tamanho g on (g.cod_grade = pro.cod_grade)
             inner join tamanho t on (t.cod_grade = pro.cod_grade and t.cod_tamanho = pro.cod_tamanho)
             LEFT OUTER JOIN fornecedor f on (cb.cod_fornece = f.cod_fornece)
            LEFT OUTER JOIN subgrupo_produto su on (su.cod_grupo = pro.cod_grupo and su.cod_subgrupo = pro.cod_subgrupo)
    where pro.cod_empresa = '1'
          and (cb.flg_estorno is null or cb.flg_estorno = 'N')
          and pfe.data >= %s
          and (pro.flg_mestre = 'N' or pro.flg_mestre is null)
    group by pro.cod_grupo, gu.des_grupo, pro.cod_subgrupo, su.des_subgrupo,
                 pro.cod_produto, pro.des_produto,  pro.cod_barra, pro.cod_referencia,
                 pro.vlr_custo_bruto, pro.vlr_custo_aquis, pro.vlr_venda1,
                 pro.cod_grade, g.des_grade, e.saldo_estoque,
                 pro.cod_tamanho, t.des_tamanho,
                 pro.cod_cor,  c.des_cor,
                 pro.dat_cadastro,pro.dat_ultcompra, cb.cod_fornece,
                 f.raz_fornece, f.fan_fornece,
                 m.cod_marca, m.nom_marca,
                 pfe.tipo_movto, pfe.qtd_movto, data_movto, pfe.cod_movto, pfe.cod_origem_movto
        order by 1, 2, 3, 4''', data_movto_ini)
            dados_estoque = cursor.fetchall()
        return dados_estoque
