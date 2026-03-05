#!/usr/bin/env python
"""
Quick script to test backend and database connectivity.
Run this from the project root: python test_backend.py
"""
import sys
import os

# Add backend/app to path (where the code expects to run from)
backend_app_path = os.path.join(os.path.dirname(__file__), 'backend', 'app')
sys.path.insert(0, backend_app_path)
# Also add backend root for db_mongo
backend_root = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_root)

def test_imports():
    """Test if backend modules can be imported."""
    print("=" * 60)
    print("1. TESTING BACKEND IMPORTS")
    print("=" * 60)
    try:
        # Change to backend/app directory for imports to work
        original_cwd = os.getcwd()
        backend_app_dir = os.path.join(os.path.dirname(__file__), 'backend', 'app')
        os.chdir(backend_app_dir)
        try:
            from main import app
            print("[OK] Backend imports successful")
            return True
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test PostgreSQL database connection."""
    print("\n" + "=" * 60)
    print("2. TESTING DATABASE CONNECTION")
    print("=" * 60)
    try:
        original_cwd = os.getcwd()
        backend_app_dir = os.path.join(os.path.dirname(__file__), 'backend', 'app')
        os.chdir(backend_app_dir)
        try:
            from db_postgres.connection import CursorFromConnectionFromPool, PostgresDatabase
            from config import settings
            
            print(f"Database: {settings.POSTGRES_DATABASE}")
            print(f"Host: {settings.POSTGRES_HOST}")
            print(f"Port: {settings.POSTGRES_PORT}")
            print(f"User: {settings.POSTGRES_USER}")
            
            # Initialize connection pool
            PostgresDatabase.initialise(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DATABASE,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT
            )
            
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"[OK] Database connection successful!")
                print(f"   PostgreSQL version: {version[0][:50]}...")
            return True
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_usuarios_table():
    """Test if USUARIOS table exists and is accessible."""
    print("\n" + "=" * 60)
    print("3. TESTING USUARIOS TABLE")
    print("=" * 60)
    try:
        original_cwd = os.getcwd()
        backend_app_dir = os.path.join(os.path.dirname(__file__), 'backend', 'app')
        os.chdir(backend_app_dir)
        try:
            from db_postgres.connection import CursorFromConnectionFromPool, PostgresDatabase
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
            
            with CursorFromConnectionFromPool() as cursor:
                # Try uppercase first
                try:
                    cursor.execute("SELECT COUNT(*) FROM USUARIOS;")
                    count = cursor.fetchone()[0]
                    print(f"[OK] USUARIOS table found (uppercase)")
                    print(f"   Total records: {count}")
                    
                    # Try to get a few sample records
                    cursor.execute("""
                        SELECT cod_usuario, nom_usuario, flg_ativo 
                        FROM USUARIOS 
                        LIMIT 5
                    """)
                    samples = cursor.fetchall()
                    print(f"   Sample records:")
                    for row in samples:
                        print(f"     - {row[0]}: {row[1]} (ativo: {row[2]})")
                    return True
                except Exception as e1:
                    print(f"   USUARIOS (uppercase) failed: {e1}")
                    # Try lowercase
                    try:
                        cursor.execute("SELECT COUNT(*) FROM usuarios;")
                        count = cursor.fetchone()[0]
                        print(f"[OK] usuarios table found (lowercase)")
                        print(f"   Total records: {count}")
                        return True
                    except Exception as e2:
                        print(f"[ERROR] usuarios (lowercase) also failed: {e2}")
                        return False
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"❌ Error testing USUARIOS table: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vendedor_endpoint():
    """Test the vendedor endpoint query."""
    print("\n" + "=" * 60)
    print("4. TESTING VENDEDOR QUERY")
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
            
            results = VendedorPostgres.get_vendedores_ativos()
            print(f"[OK] Query successful!")
            print(f"   Found {len(results)} vendedores")
            if results:
                print(f"   First 3 vendedores:")
                for v in results[:3]:
                    print(f"     - {v.get('cod_vendedor')}: {v.get('nom_vendedor')}")
            return True
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BACKEND & DATABASE DIAGNOSTIC TOOL")
    print("=" * 60 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Database Connection": test_database_connection(),
        "USUARIOS Table": test_usuarios_table(),
        "Vendedor Query": test_vendedor_endpoint()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] ALL TESTS PASSED - Backend and database are working!")
    else:
        print("[ERROR] SOME TESTS FAILED - Check the errors above")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
