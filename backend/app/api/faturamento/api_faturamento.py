from fastapi import APIRouter, HTTPException, Query
from .faturamento_postgres import FaturamentoPostgres
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/faturamento/brand")
async def get_faturamento_by_brand(
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get faturamento grouped by brand."""
    try:
        logger.info(f"API endpoint called: Getting faturamento by brand for period: {data_ini} to {data_fim}")
        logger.info(f"Received parameters - data_ini: {data_ini} (type: {type(data_ini)}), data_fim: {data_fim} (type: {type(data_fim)})")
        results = FaturamentoPostgres.get_faturamento_by_brand(data_ini, data_fim)
        logger.info(f"Query completed. Found {len(results) if results else 0} brands")
        if not results:
            logger.warning(f"No brands returned for period {data_ini} to {data_fim} - this may indicate no data or all filtered out")
        # Return empty list if no data (don't raise error for date ranges with no sales)
        return results if results else []
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"ERROR in get_faturamento_by_brand API endpoint: {error_msg}\n{error_traceback}", exc_info=True)
        # Return empty list instead of 500 for date ranges with no data
        # But log the full error for debugging
        # IMPORTANT: Check backend logs if you see empty results
        return []


@router.get("/api/faturamento/product")
async def get_faturamento_by_product(
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)"),
    cod_marca: Optional[int] = Query(None, description="Filter by brand code"),
    include_devolucoes_estornos: bool = Query(False, description="Include devoluções and estornos")
):
    """Get faturamento grouped by product with margins."""
    try:
        results = FaturamentoPostgres.get_faturamento_by_product(
            data_ini, data_fim, cod_marca, include_devolucoes_estornos
        )
        return results
    except Exception as e:
        logger.error(f"Error getting faturamento by product: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/faturamento/size")
async def get_faturamento_by_size(
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)"),
    cod_marca: Optional[int] = Query(None, description="Filter by brand code")
):
    """Get faturamento grouped by size."""
    try:
        results = FaturamentoPostgres.get_faturamento_by_size(data_ini, data_fim, cod_marca)
        return results
    except Exception as e:
        logger.error(f"Error getting faturamento by size: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/faturamento/collection")
async def get_faturamento_by_collection(
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get faturamento grouped by collection (winter/summer)."""
    try:
        results = FaturamentoPostgres.get_faturamento_by_collection(data_ini, data_fim)
        return results
    except Exception as e:
        logger.error(f"Error getting faturamento by collection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/faturamento/promotion-only")
async def get_products_promotion_only(
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get products that only sell on promotion (for alerts)."""
    try:
        results = FaturamentoPostgres.get_products_promotion_only(data_ini, data_fim)
        return results
    except Exception as e:
        logger.error(f"Error getting promotion-only products: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/faturamento/movimentos")
async def get_movimentos_by_referencia_cor(
    cod_referencia: str = Query(..., description="Product reference code"),
    cod_cor: str = Query(..., description="Color code (as string, will be converted to int)"),
    data_ini: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)"),
    include_devolucoes_estornos: bool = Query(False, description="Include devoluções and estornos")
):
    """Get detailed movimentos (sales) by referencia and cor, grouped by grade."""
    try:
        # Convert cod_cor to int (FastAPI might receive it as string from query params)
        try:
            cod_cor_int = int(cod_cor)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Invalid cod_cor: {cod_cor}. Must be a number.")
        
        results = FaturamentoPostgres.get_movimentos_by_referencia_cor(
            cod_referencia, cod_cor_int, data_ini, data_fim, include_devolucoes_estornos
        )
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting movimentos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
