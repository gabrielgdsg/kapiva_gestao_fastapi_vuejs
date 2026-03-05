"""
Script to extract ALL unique GRADE GROUPS (combinations of sizes) from the database.
A grade group is like: (33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44)
Grades that are entirely contained in another grade are removed.
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

# Load environment variables
env_file = project_root / 'develop_pycharm.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

def extract_grade_groups():
    """Extract all unique grade groups from the database."""
    
    print("=" * 80)
    print("EXTRACTING ALL UNIQUE GRADE GROUPS FROM DATABASE")
    print("=" * 80)
    print()
    
    # Initialize database connection
    PostgresDatabase.initialise(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DATABASE,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    
    with CursorFromConnectionFromPool() as cursor:
        # Query: Get all unique grade groups with their sizes
        # Group by cod_grade to get all sizes that belong to each grade
        cursor.execute('''
            SELECT 
                g.cod_grade,
                g.des_grade,
                t.des_tamanho,
                COUNT(DISTINCT pro.cod_produto) as product_count,
                COUNT(DISTINCT pro.cod_referencia) as reference_count,
                COUNT(DISTINCT m.cod_marca) as brand_count
            FROM grade_tamanho g
            INNER JOIN tamanho t ON (t.cod_grade = g.cod_grade)
            LEFT JOIN PRODUTO pro ON (
                pro.cod_grade = g.cod_grade 
                AND pro.cod_tamanho = t.cod_tamanho
                AND pro.cod_empresa = '1'
            )
            LEFT JOIN MARCA m ON (m.cod_marca = pro.cod_marca)
            WHERE pro.cod_produto IS NOT NULL
            GROUP BY g.cod_grade, g.des_grade, t.des_tamanho
            ORDER BY g.cod_grade, t.des_tamanho
        ''')
        
        results = cursor.fetchall()
        
        # Group by cod_grade to build grade groups
        grade_groups = defaultdict(lambda: {
            'des_grade': '',
            'sizes': set(),
            'product_count': 0,
            'reference_count': 0,
            'brand_count': 0,
            'size_details': []
        })
        
        for row in results:
            cod_grade = row[0]
            des_grade = row[1] or ''
            des_tamanho = row[2] or ''
            product_count = row[3] or 0
            reference_count = row[4] or 0
            brand_count = row[5] or 0
            
            grade_groups[cod_grade]['des_grade'] = des_grade
            grade_groups[cod_grade]['sizes'].add(des_tamanho)
            grade_groups[cod_grade]['product_count'] += product_count
            grade_groups[cod_grade]['reference_count'] = max(
                grade_groups[cod_grade]['reference_count'], 
                reference_count
            )
            grade_groups[cod_grade]['brand_count'] = max(
                grade_groups[cod_grade]['brand_count'],
                brand_count
            )
            grade_groups[cod_grade]['size_details'].append({
                'des_tamanho': des_tamanho,
                'product_count': product_count
            })
        
        # Convert sets to sorted lists
        grade_list = []
        for cod_grade, data in grade_groups.items():
            sizes_list = sorted(list(data['sizes']))
            grade_list.append({
                'cod_grade': cod_grade,
                'des_grade': data['des_grade'],
                'sizes': sizes_list,
                'sizes_count': len(sizes_list),
                'product_count': data['product_count'],
                'reference_count': data['reference_count'],
                'brand_count': data['brand_count'],
                'sizes_str': ';'.join(sizes_list)  # Format: 33;34;35;36...
            })
        
        # Sort by number of sizes (largest first)
        grade_list.sort(key=lambda x: x['sizes_count'], reverse=True)
        
        print(f"Total grade groups found: {len(grade_list)}")
        print()
        
        # Remove grades that are entirely contained in other grades
        print("Removing grades that are entirely contained in other grades...")
        filtered_grades = []
        for grade in grade_list:
            is_subset = False
            grade_sizes_set = set(grade['sizes'])
            
            # Check if this grade is a subset of any other grade
            for other_grade in grade_list:
                if grade['cod_grade'] == other_grade['cod_grade']:
                    continue
                other_sizes_set = set(other_grade['sizes'])
                
                # If all sizes in this grade are in another grade, it's a subset
                if grade_sizes_set.issubset(other_sizes_set):
                    is_subset = True
                    print(f"  Removing '{grade['des_grade']}' ({grade['sizes_count']} sizes) - "
                          f"contained in '{other_grade['des_grade']}' ({other_grade['sizes_count']} sizes)")
                    break
            
            if not is_subset:
                filtered_grades.append(grade)
        
        print(f"\nAfter filtering: {len(filtered_grades)} unique grade groups")
        print()
        
        # Print results
        print("=" * 80)
        print("ALL UNIQUE GRADE GROUPS (after removing subsets)")
        print("=" * 80)
        print()
        
        for grade in filtered_grades:
            print(f"\n[GRADE] {grade['des_grade']} (cod_grade: {grade['cod_grade']})")
            print(f"  Sizes ({grade['sizes_count']}): {grade['sizes_str']}")
            print(f"  Products: {grade['product_count']} | Refs: {grade['reference_count']} | Brands: {grade['brand_count']}")
        
        # Print in format for easy copy-paste
        print()
        print("=" * 80)
        print("FORMATTED FOR LEVANTAMENTOS (copy-paste ready)")
        print("=" * 80)
        print()
        print("grades_options: [")
        for grade in filtered_grades:
            sizes_formatted = ', '.join([f"'{s}'" for s in grade['sizes']])
            print(f"  {{")
            print(f"    name: '{grade['des_grade']}',")
            print(f"    grade: [{sizes_formatted}]")
            print(f"  }},")
        print("]")
        
        # Save to JSON
        output_file = project_root / 'all_grade_groups_extracted.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_grade_groups': len(filtered_grades),
                'grade_groups': filtered_grades,
                'formatted_for_levantamentos': [
                    {
                        'name': g['des_grade'],
                        'grade': [{'key': s, 'label': s} for s in g['sizes']]
                    }
                    for g in filtered_grades
                ]
            }, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"[SUCCESS] Results saved to: {output_file}")
        print()
        
        return filtered_grades

if __name__ == '__main__':
    try:
        results = extract_grade_groups()
        print("\n[SUCCESS] Extraction complete!")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
