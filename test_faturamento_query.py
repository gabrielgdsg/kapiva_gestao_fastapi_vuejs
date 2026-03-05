#!/usr/bin/env python3
"""
Test script to diagnose faturamento query issues.
Run this from the project root: python test_faturamento_query.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
backend_dir = project_root / "backend"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.faturamento.faturamento_postgres import FaturamentoPostgres
from app.core.logging import setup_logging, get_logger
from app.db_postgres.connection import PostgresDatabase
from app.config import settings

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize database connection pool
try:
    PostgresDatabase.initialise(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DATABASE,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    logger.info(f"Database connection pool initialized for {settings.POSTGRES_DATABASE}")
except Exception as e:
    logger.error(f"Failed to initialize database connection pool: {str(e)}")
    print(f"❌ Failed to initialize database: {str(e)}")
    sys.exit(1)

def test_faturamento_query():
    """Test the faturamento query with different date ranges."""
    
    # Test dates
    test_cases = [
        ("2021-12-01", "2021-12-31"),
        ("2022-01-01", "2022-01-31"),
        ("2022-12-01", "2022-12-31"),
        ("2023-01-01", "2023-01-31"),
    ]
    
    print("=" * 80)
    print("TESTING FATURAMENTO QUERIES")
    print("=" * 80)
    
    for data_ini, data_fim in test_cases:
        print(f"\n{'='*80}")
        print(f"Testing period: {data_ini} to {data_fim}")
        print(f"{'='*80}")
        
        try:
            results = FaturamentoPostgres.get_faturamento_by_brand(data_ini, data_fim)
            print(f"✅ Query executed successfully")
            print(f"   Found {len(results)} brands")
            
            if results:
                print(f"\n   First 3 brands:")
                for i, brand in enumerate(results[:3], 1):
                    print(f"   {i}. {brand.get('nom_marca', 'N/A')} - "
                          f"Vlr Bruto: {brand.get('vlr_bruto_total', 0):,.2f}")
            else:
                print(f"   ⚠️  No brands returned")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print("=" * 80)
    
    # Close database connections
    try:
        PostgresDatabase.close_all_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {str(e)}")

if __name__ == "__main__":
    test_faturamento_query()
