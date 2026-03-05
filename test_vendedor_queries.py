#!/usr/bin/env python
"""
Test script to check vendedor queries directly.
Run: python test_vendedor_queries.py
"""
import sys
import os

# Add backend/app to path
backend_app_path = os.path.join(os.path.dirname(__file__), 'backend', 'app')
sys.path.insert(0, backend_app_path)

def test_monthly_query():
    """Test the monthly summary query."""
    print("=" * 60)
    print("Testing get_vendas_monthly_summary")
    print("=" * 60)
    try:
        original_cwd = os.getcwd()
        backend_app_dir = os.path.join(os.path.dirname(__file__), 'backend', 'app')
        os.chdir(backend_app_dir)
        try:
            from api.vendedor.vendedor_postgres import VendedorPostgres
            from db_postgres.connection import PostgresDatabase
            from config import settings
            
            # Initialize database
            PostgresDatabase.initialise(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DATABASE,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT
            )
            
            results = VendedorPostgres.get_vendas_monthly_summary(7, 2024)
            print(f"[OK] Query successful! Found {len(results)} months")
            if results:
                print("Sample results:")
                for r in results[:3]:
                    print(f"  Month {r.get('mes')}: R$ {r.get('vlr_liquido_total')}")
            return True
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vendas_by_day():
    """Test the vendas by day query."""
    print("\n" + "=" * 60)
    print("Testing get_vendas_by_day")
    print("=" * 60)
    try:
        original_cwd = os.getcwd()
        backend_app_dir = os.path.join(os.path.dirname(__file__), 'backend', 'app')
        os.chdir(backend_app_dir)
        try:
            from api.vendedor.vendedor_postgres import VendedorPostgres
            from db_postgres.connection import PostgresDatabase
            from config import settings
            
            # Initialize if not already done
            try:
                PostgresDatabase.initialise(
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    database=settings.POSTGRES_DATABASE,
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT
                )
            except:
                pass  # Already initialized
            
            results = VendedorPostgres.get_vendas_by_day(7, '2024-01-01', '2024-12-31')
            print(f"[OK] Query successful! Found {len(results)} days")
            if results:
                print("Sample results:")
                for r in results[:3]:
                    print(f"  {r.get('data_venda')}: R$ {r.get('vlr_liquido_total')}")
            return True
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("VENDEDOR QUERIES TEST")
    print("=" * 60 + "\n")
    
    test_monthly_query()
    test_vendas_by_day()
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60 + "\n")
