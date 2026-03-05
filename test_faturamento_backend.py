"""
Test script to diagnose faturamento backend endpoint
"""
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory for imports
os.chdir(backend_path)

from app.db_postgres.connection import PostgresDatabase, CursorFromConnectionFromPool
from app.config import settings
from app.api.faturamento.faturamento_postgres import FaturamentoPostgres
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
PostgresDatabase.initialise(
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    database=settings.POSTGRES_DATABASE,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT
)

print("=" * 80)
print("TESTING FATURAMENTO BACKEND")
print("=" * 80)

data_ini = '2022-01-01'
data_fim = '2022-01-31'

print(f"\nTesting period: {data_ini} to {data_fim}\n")

# Test 1: Direct database query
print("-" * 80)
print("TEST 1: Direct Database Query")
print("-" * 80)

try:
    with CursorFromConnectionFromPool() as cursor:
        # Count total invoices
        cursor.execute('''
            SELECT COUNT(*)
            FROM nota_fiscal nf
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
        ''', (data_ini, data_fim))
        total_nf = cursor.fetchone()[0]
        print(f"Total invoices in period: {total_nf}")
        
        # Count after filters
        cursor.execute('''
            SELECT COUNT(*)
            FROM nota_fiscal nf
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
              AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
              AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
        ''', (data_ini, data_fim))
        after_filters = cursor.fetchone()[0]
        print(f"After filters (not canceled, not devolução): {after_filters}")
        
        # Count items with joins
        cursor.execute('''
            SELECT COUNT(*)
            FROM nota_fiscal nf
            JOIN item_nf i ON i.nf_interno = nf.nf_interno
            JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
              AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
              AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
        ''', (data_ini, data_fim))
        items_count = cursor.fetchone()[0]
        print(f"Items after joins: {items_count}")
        
        # Get totals
        cursor.execute('''
            SELECT 
                SUM(i.vlr_total) as total_bruto_all,
                SUM(i.vlr_total - COALESCE(i.desc_rat, 0)) - SUM(i.qtd_produto * 
                    CASE 
                        WHEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        ) > 1.00
                        THEN GREATEST(
                            COALESCE(p.vlr_custo_bruto_medio, 0), 
                            COALESCE(p.vlr_custo_medio, 0), 
                            COALESCE(p.vlr_custo_aquis, 0)
                        )
                        ELSE COALESCE(p.vlr_venda1, 0) / 2.0
                    END
                ) as total_lucro_all
            FROM nota_fiscal nf
            JOIN item_nf i ON i.nf_interno = nf.nf_interno
            JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
              AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
              AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
        ''', (data_ini, data_fim))
        totals = cursor.fetchone()
        total_bruto_all = float(totals[0]) if totals[0] is not None else 0.0
        total_lucro_all = float(totals[1]) if totals[1] is not None else 0.0
        print(f"Total bruto all: {total_bruto_all}")
        print(f"Total lucro all: {total_lucro_all}")
        
        if total_bruto_all == 0 and total_lucro_all == 0:
            print("\n⚠️  WARNING: Totals are 0 - this will cause early return!")
        
        # Count brands
        cursor.execute('''
            SELECT COUNT(DISTINCT m.cod_marca)
            FROM nota_fiscal nf
            JOIN item_nf i ON i.nf_interno = nf.nf_interno
            JOIN produto p ON p.cod_produto = i.cod_produto AND p.cod_empresa = i.cod_empresa
            JOIN marca m ON m.cod_marca = p.cod_marca
            WHERE nf.dat_emissao::date >= %s::date
              AND nf.dat_emissao::date <= %s::date
              AND (nf.flg_cancelado IS NULL OR nf.flg_cancelado != 'S')
              AND (nf.cod_grupo_operacoes IS NULL OR nf.cod_grupo_operacoes != 6)
        ''', (data_ini, data_fim))
        brands_count = cursor.fetchone()[0]
        print(f"Distinct brands: {brands_count}")
        
except Exception as e:
    print(f"❌ ERROR in direct query: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Using the actual method
print("\n" + "-" * 80)
print("TEST 2: Using FaturamentoPostgres.get_faturamento_by_brand()")
print("-" * 80)

try:
    results = FaturamentoPostgres.get_faturamento_by_brand(data_ini, data_fim)
    print(f"Results returned: {len(results) if results else 0} brands")
    if results:
        print("\nFirst 3 brands:")
        for i, brand in enumerate(results[:3]):
            print(f"  {i+1}. {brand.get('nom_marca', 'N/A')} - {brand.get('vlr_bruto_total', 0)}")
    else:
        print("⚠️  No brands returned!")
except Exception as e:
    print(f"❌ ERROR in get_faturamento_by_brand: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
