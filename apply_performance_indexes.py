#!/usr/bin/env python3
"""
Apply Performance Indexes to PostgreSQL Database
Created: 2026-01-11
Purpose: Automatically create all performance indexes for the levantamentos query
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "app"
sys.path.insert(0, str(backend_path))

from db_postgres.connection import CursorFromConnectionFromPool, PostgresDatabase
from config import settings

def create_indexes():
    """Create all performance indexes"""
    
    # Initialize database connection pool
    PostgresDatabase.initialise(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DATABASE,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    
    indexes = [
        # Critical combined index
        ("""
        CREATE INDEX IF NOT EXISTS idx_produto_empresa_marca_cadastro 
            ON PRODUTO(cod_empresa, cod_marca, dat_cadastro)
            WHERE (flg_mestre = 'N' OR flg_mestre IS NULL)
        """, "Combined empresa+marca+cadastro index"),
        
        # Date sorting index
        ("""
        CREATE INDEX IF NOT EXISTS idx_produto_cadastro_ultcompra 
            ON PRODUTO(dat_cadastro DESC, dat_ultcompra DESC NULLS LAST)
            WHERE cod_empresa = '1'
        """, "Date sorting index"),
        
        # Foreign key indexes
        ("""CREATE INDEX IF NOT EXISTS idx_produto_marca ON PRODUTO(cod_marca) WHERE cod_marca IS NOT NULL""", 
         "Marca FK index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_produto_grade ON PRODUTO(cod_grade)""", 
         "Grade FK index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_produto_grade_tamanho ON PRODUTO(cod_grade, cod_tamanho)""", 
         "Grade+Tamanho FK index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_produto_cor ON PRODUTO(cod_cor) WHERE cod_cor IS NOT NULL""", 
         "Cor FK index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_produto_grupo_subgrupo ON PRODUTO(cod_grupo, cod_subgrupo)""", 
         "Grupo+Subgrupo FK index"),
        
        # NFCompra indexes
        ("""CREATE INDEX IF NOT EXISTS idx_nfcompraitem_empresa_produto ON nfcompraitem(cod_empresa, cod_produto)""", 
         "NFCompraItem join index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_nfcompra_empresa_interno ON nfcompra(cod_empresa, cod_interno)""", 
         "NFCompra join index"),
        
        ("""
        CREATE INDEX IF NOT EXISTS idx_nfcompra_estorno 
            ON nfcompra(cod_empresa, cod_interno, flg_estorno)
            WHERE (flg_estorno IS NULL OR flg_estorno = 'N')
        """, "NFCompra estorno filter index"),
        
        # Other table indexes
        ("""CREATE INDEX IF NOT EXISTS idx_produto_ficha_estoq_produto ON produto_ficha_estoq(cod_produto)""", 
         "Produto ficha estoque index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_fornecedor_codigo ON fornecedor(cod_fornece)""", 
         "Fornecedor index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_marca_codigo ON MARCA(COD_MARCA)""", 
         "Marca index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_grade_tamanho_codigo ON grade_tamanho(cod_grade)""", 
         "Grade tamanho index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_tamanho_grade_codigo ON tamanho(cod_grade, cod_tamanho)""", 
         "Tamanho index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_cores_codigo ON cores(cod_cor)""", 
         "Cores index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_grupo_produto_codigo ON grupo_produto(cod_grupo)""", 
         "Grupo produto index"),
        
        ("""CREATE INDEX IF NOT EXISTS idx_subgrupo_produto_codigo ON subgrupo_produto(cod_grupo, cod_subgrupo)""", 
         "Subgrupo produto index"),
    ]
    
    analyze_tables = [
        "PRODUTO", "nfcompraitem", "nfcompra", "produto_ficha_estoq",
        "MARCA", "grade_tamanho", "tamanho", "cores", 
        "grupo_produto", "subgrupo_produto", "fornecedor"
    ]
    
    print("=" * 60)
    print("CREATING PERFORMANCE INDEXES")
    print("=" * 60)
    print(f"Database: {settings.POSTGRES_DATABASE}")
    print(f"Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"Total indexes to create: {len(indexes)}")
    print()
    
    try:
        with CursorFromConnectionFromPool() as cursor:
            # Create indexes
            for i, (sql, description) in enumerate(indexes, 1):
                try:
                    print(f"[{i}/{len(indexes)}] Creating: {description}...", end=" ")
                    cursor.execute(sql)
                    print("OK")
                except Exception as e:
                    print(f"ERROR: {e}")
            
            # Analyze tables
            print()
            print("Updating table statistics...")
            for table in analyze_tables:
                try:
                    print(f"  Analyzing {table}...", end=" ")
                    cursor.execute(f"ANALYZE {table}")
                    print("OK")
                except Exception as e:
                    print(f"ERROR: {e}")
            
            # Commit changes
            cursor.connection.commit()
            
        print()
        print("=" * 60)
        print("INDEX CREATION COMPLETE!")
        print("=" * 60)
        print()
        print("Expected improvements:")
        print("  - Query execution: 5-10x faster")
        print("  - Better date range filtering")
        print("  - Efficient JOIN operations")
        print("  - Optimized sorting")
        print()
        print("Next steps:")
        print("  1. Restart the backend server")
        print("  2. Test the levantamentos endpoint")
        print("  3. Check query performance")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR CREATING INDEXES")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Please check:")
        print("  1. Database connection settings")
        print("  2. User has CREATE INDEX privilege")
        print("  3. Tables exist in database")
        sys.exit(1)

def check_indexes():
    """Check which indexes already exist"""
    print("Checking existing indexes...")
    print()
    
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute("""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
                AND tablename IN ('produto', 'nfcompraitem', 'nfcompra', 'produto_ficha_estoq',
                                 'marca', 'grade_tamanho', 'tamanho', 'cores',
                                 'grupo_produto', 'subgrupo_produto', 'fornecedor')
            ORDER BY tablename, indexname
        """)
        
        results = cursor.fetchall()
        
        if results:
            current_table = None
            for row in results:
                tablename, indexname, _ = row
                if tablename != current_table:
                    print(f"\n{tablename.upper()}:")
                    current_table = tablename
                print(f"  - {indexname}")
        else:
            print("No custom indexes found.")
    
    print()

if __name__ == "__main__":
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_indexes()
    else:
        # Show warning
        print("WARNING: This will create multiple indexes on your database.")
        print("         This may take 5-15 minutes depending on table sizes.")
        print()
        
        response = input("Do you want to continue? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            print()
            create_indexes()
        else:
            print("Aborted.")
            sys.exit(0)
