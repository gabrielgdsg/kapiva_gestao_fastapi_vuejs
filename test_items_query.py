#!/usr/bin/env python
"""
Test script to check items query directly.
Run: python test_items_query.py
"""
import sys
import os

# Add backend/app to path
backend_app_path = os.path.join(os.path.dirname(__file__), 'backend', 'app')
sys.path.insert(0, backend_app_path)

def test_items_query():
    """Test the items query."""
    print("=" * 60)
    print("Testing get_vendas_items_by_nf")
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
            
            results = VendedorPostgres.get_vendas_items_by_nf(25197)
            print(f"[OK] Query successful! Found {len(results)} items")
            if results:
                print("Sample results:")
                for r in results[:3]:
                    print(f"  Item {r.get('cod_sequencial')}: {r.get('des_produto')} - R$ {r.get('vlr_liquido')}")
            else:
                print("  No items found for this invoice")
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
    print("ITEMS QUERY TEST")
    print("=" * 60 + "\n")
    
    test_items_query()
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60 + "\n")
