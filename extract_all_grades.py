"""
Script to extract ALL unique grades (sizes) from the database
and generate a comprehensive list for review and filtering.
"""
import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent
backend_path = project_root / 'backend'
sys.path.insert(0, str(backend_path))

from app.db_postgres.connection import CursorFromConnectionFromPool, PostgresDatabase
from app.config import settings
from collections import defaultdict
import json
import os

# Load environment variables
from pathlib import Path
env_file = project_root / 'develop_pycharm.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

def extract_all_grades():
    # Initialize database connection with settings
    PostgresDatabase.initialise(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DATABASE,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    """Extract all unique grades from the database."""
    
    print("=" * 80)
    print("EXTRACTING ALL UNIQUE GRADES FROM DATABASE")
    print("=" * 80)
    print()
    
    with CursorFromConnectionFromPool() as cursor:
        # Query 1: Get all unique tamanhos (grades) with their usage count
        cursor.execute('''
            SELECT 
                t.des_tamanho,
                g.des_grade,
                COUNT(DISTINCT pro.cod_produto) as product_count,
                COUNT(DISTINCT pro.cod_referencia) as reference_count,
                COUNT(DISTINCT m.cod_marca) as brand_count
            FROM tamanho t
            INNER JOIN grade_tamanho g ON (g.cod_grade = t.cod_grade)
            LEFT JOIN PRODUTO pro ON (
                pro.cod_grade = t.cod_grade 
                AND pro.cod_tamanho = t.cod_tamanho
                AND pro.cod_empresa = '1'
            )
            LEFT JOIN MARCA m ON (m.cod_marca = pro.cod_marca)
            WHERE pro.cod_produto IS NOT NULL
            GROUP BY t.des_tamanho, g.des_grade
            ORDER BY t.des_tamanho
        ''')
        
        results = cursor.fetchall()
        
        # Organize grades by type
        grades_by_type = defaultdict(list)
        all_grades = []
        
        for row in results:
            des_tamanho = row[0] or ''
            des_grade = row[1] or ''
            product_count = row[2] or 0
            reference_count = row[3] or 0
            brand_count = row[4] or 0
            
            grade_info = {
                'des_tamanho': des_tamanho,
                'des_grade': des_grade,
                'product_count': product_count,
                'reference_count': reference_count,
                'brand_count': brand_count
            }
            
            all_grades.append(grade_info)
            grades_by_type[des_grade].append(grade_info)
        
        # Print summary
        print(f"Total unique grades found: {len(all_grades)}")
        print(f"Total grade types (des_grade): {len(grades_by_type)}")
        print()
        
        # Print by grade type
        print("=" * 80)
        print("GRADES GROUPED BY GRADE TYPE (des_grade)")
        print("=" * 80)
        print()
        
        for grade_type, grades in sorted(grades_by_type.items()):
            print(f"\n[GRADE TYPE] {grade_type} ({len(grades)} sizes)")
            print("-" * 80)
            for grade in sorted(grades, key=lambda x: x['des_tamanho']):
                print(f"  • {grade['des_tamanho']:15} | "
                      f"Products: {grade['product_count']:6} | "
                      f"Refs: {grade['reference_count']:5} | "
                      f"Brands: {grade['brand_count']:3}")
        
        # Print all unique sizes (sorted)
        print()
        print("=" * 80)
        print("ALL UNIQUE SIZES (SORTED ALPHANUMERICALLY)")
        print("=" * 80)
        print()
        
        unique_sizes = sorted(set([g['des_tamanho'] for g in all_grades]))
        
        # Group for display
        print("All sizes:")
        print(", ".join(unique_sizes))
        print()
        print(f"Total: {len(unique_sizes)} unique sizes")
        
        # Print JSON format for easy copy-paste
        print()
        print("=" * 80)
        print("JSON FORMAT (for easy filtering/concat)")
        print("=" * 80)
        print()
        print(json.dumps({
            'total_unique_sizes': len(unique_sizes),
            'all_sizes': unique_sizes,
            'by_grade_type': {
                grade_type: [g['des_tamanho'] for g in sorted(grades, key=lambda x: x['des_tamanho'])]
                for grade_type, grades in sorted(grades_by_type.items())
            },
            'detailed': all_grades
        }, indent=2, ensure_ascii=False))
        
        # Save to file
        output_file = project_root / 'all_grades_extracted.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_unique_sizes': len(unique_sizes),
                'all_sizes': unique_sizes,
                'by_grade_type': {
                    grade_type: [g['des_tamanho'] for g in sorted(grades, key=lambda x: x['des_tamanho'])]
                    for grade_type, grades in sorted(grades_by_type.items())
                },
                'detailed': all_grades
            }, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"✅ Results saved to: {output_file}")
        print()
        
        return {
            'all_sizes': unique_sizes,
            'by_grade_type': grades_by_type,
            'detailed': all_grades
        }

if __name__ == '__main__':
    try:
        results = extract_all_grades()
        print("\n[SUCCESS] Extraction complete!")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
