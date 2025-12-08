from fastapi import APIRouter, HTTPException
from db_postgres.connection import CursorFromConnectionFromPool

router = APIRouter()

@router.get("/api/vendas/{cod_vendedor}/{date}")
async def get_vendas(cod_vendedor: int, date: str):
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute('''SELECT cod_vendedor, nom_vendedor, base_calculo, cod_origem, tipo_origem
                              FROM (SELECT A.cod_vendedor, AB.nom_usuario AS nom_vendedor, 
                                           (a.base_calc_comissao) AS base_calculo, a.cod_origem, a.tipo_origem
                                    FROM COMISSAO A
                                    LEFT OUTER JOIN USUARIOS AB ON (A.cod_vendedor = AB.cod_usuario)
                                    WHERE A.dat_emissao = %s AND cod_vendedor = %s
                                    GROUP BY cod_vendedor, nom_vendedor, base_calculo, a.cod_origem, a.tipo_origem) resultado_busca
                              GROUP BY nom_vendedor, cod_vendedor, base_calculo, cod_origem, tipo_origem
                              ORDER BY cod_vendedor DESC''', (date, cod_vendedor))
            vendas = cursor.fetchall()
            if not vendas:
                raise HTTPException(status_code=404, detail="No sales found for the given date.")
            return vendas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


vendedor_urls = {
    74: "1234",
    75: "5678",
    # Add more mappings here
}

@router.get("/api/vendedor/{cod_vendedor}")
async def get_vendedor_url(cod_vendedor: int):
    if cod_vendedor not in vendedor_urls:
        raise HTTPException(status_code=404, detail="Vendedor not found.")
    return {"url": f"/vendedor/{cod_vendedor}/{vendedor_urls[cod_vendedor]}"}