"""
Quick import test to verify all modules can be imported correctly.
This tests that our refactoring didn't break any imports.
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all critical modules can be imported."""
    errors = []
    
    try:
        from config import settings
        print("[OK] Config import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Config import failed: {e}")
    
    try:
        from core.logging import setup_logging, get_logger
        print("[OK] Logging import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Logging import failed: {e}")
    
    try:
        from db_postgres.connection import PostgresDatabase, CursorFromConnectionFromPool
        print("[OK] Postgres connection import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Postgres connection import failed: {e}")
    
    try:
        from db_mongo.database import engine, init_db
        print("[OK] MongoDB import: OK")
    except Exception as e:
        errors.append(f"[ERROR] MongoDB import failed: {e}")
    
    try:
        from api.comissao import api_comissao
        print("[OK] Comissao API import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Comissao API import failed: {e}")
    
    try:
        from api.vendas.api_vendas import router as vendas_router
        print("[OK] Vendas API import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Vendas API import failed: {e}")
    
    try:
        from api.estoque import api_estoque
        print("[OK] Estoque API import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Estoque API import failed: {e}")
    
    try:
        from api.financeiro import api_caixa
        print("[OK] Financeiro API import: OK")
    except Exception as e:
        errors.append(f"[ERROR] Financeiro API import failed: {e}")
    
    if errors:
        print("\n[ERRORS FOUND]")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n[SUCCESS] All imports successful!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
