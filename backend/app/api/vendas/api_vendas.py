from fastapi import APIRouter, HTTPException
from app.db_postgres.connection import CursorFromConnectionFromPool
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/vendas/{cod_vendedor}/{date}")
async def get_vendas(cod_vendedor: int, date: str):
    """
    Get sales data for a specific vendor and date.
    Uses COMISSAO table as the single source of truth (PROJECT_RULES Section 9.1).
    
    Args:
        cod_vendedor: Vendor code
        date: Sales date (YYYY-MM-DD format)
        
    Returns:
        List of sales records with base_calc_comissao from COMISSAO table
    """
    try:
        with CursorFromConnectionFromPool() as cursor:
            # IMPORTANT: This query uses COMISSAO table as single source of truth
            # Do not modify the query logic - only error handling around it
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
                logger.info(f"No sales found for vendor {cod_vendedor} on date {date}")
                raise HTTPException(status_code=404, detail=f"No sales found for vendor {cod_vendedor} on date {date}.")
            logger.debug(f"Retrieved {len(vendas)} sales records for vendor {cod_vendedor} on {date}")
            return vendas
    except HTTPException:
        # Re-raise HTTP exceptions as-is (404, etc.)
        raise
    except Exception as e:
        # Log full error internally, but don't expose to client
        logger.error(f"Error retrieving sales for vendor {cod_vendedor} on date {date}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while retrieving sales data. Please contact support if this persists."
        )


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