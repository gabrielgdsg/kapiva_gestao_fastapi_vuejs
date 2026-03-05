"""
Extract grade groups based on ACTUAL product size combinations.
For each product (cod_referencia + cod_cor), collect all sizes that exist.
Then create grade groups and remove subsets.
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

def extract_product_grade_groups():
    """Extract grade groups from actual product size combinations."""
    
    print("=" * 80)
    print("EXTRACTING GRADE GROUPS FROM ACTUAL PRODUCT SIZE COMBINATIONS")
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
        # Query: Get all products with their actual sizes
        # Group by cod_referencia + cod_cor to get size combinations per product variant
        cursor.execute('''
            SELECT DISTINCT
                pro.cod_referencia,
                pro.cod_cor,
                c.des_cor,
                m.nom_marca,
                t.des_tamanho
            FROM PRODUTO pro
            INNER JOIN tamanho t ON (
                t.cod_grade = pro.cod_grade 
                AND t.cod_tamanho = pro.cod_tamanho
            )
            LEFT JOIN cores c ON (c.cod_cor = pro.cod_cor)
            LEFT JOIN MARCA m ON (m.cod_marca = pro.cod_marca)
            WHERE pro.cod_empresa = '1'
              AND (pro.flg_mestre = 'N' OR pro.flg_mestre IS NULL)
              AND t.des_tamanho IS NOT NULL
              AND t.des_tamanho != ''
            ORDER BY pro.cod_referencia, pro.cod_cor, t.des_tamanho
        ''')
        
        results = cursor.fetchall()
        
        print(f"Total product-size records found: {len(results)}")
        
        # Group by product (cod_referencia + cod_cor)
        product_grades = defaultdict(lambda: {
            'sizes': set(),
            'nom_marca': '',
            'des_cor': '',
            'size_count': 0
        })
        
        for row in results:
            cod_referencia = row[0] or ''
            cod_cor = row[1] or ''
            des_cor = row[2] or ''
            nom_marca = row[3] or ''
            des_tamanho = row[4] or ''
            
            # Create unique key for product variant
            product_key = f"{cod_referencia}_{cod_cor}"
            
            product_grades[product_key]['sizes'].add(des_tamanho)
            product_grades[product_key]['nom_marca'] = nom_marca
            product_grades[product_key]['des_cor'] = des_cor
        
        print(f"Total unique products (reference+color): {len(product_grades)}")
        print()
        
        # Convert to list of grade groups
        grade_groups = []
        for product_key, data in product_grades.items():
            sizes_list = sorted(list(data['sizes']))
            if len(sizes_list) > 0:  # Only include products with at least one size
                grade_groups.append({
                    'product_key': product_key,
                    'nom_marca': data['nom_marca'],
                    'des_cor': data['des_cor'],
                    'sizes': sizes_list,
                    'sizes_count': len(sizes_list),
                    'sizes_set': set(sizes_list),
                    'sizes_str': ';'.join(sizes_list)
                })
        
        # Sort by number of sizes (largest first)
        grade_groups.sort(key=lambda x: x['sizes_count'], reverse=True)
        
        print(f"Grade groups before filtering: {len(grade_groups)}")
        print()
        
        # Remove grade groups that are entirely contained in other grade groups
        print("Removing grade groups that are subsets of others...")
        filtered_grades = []
        removed_count = 0
        
        for grade in grade_groups:
            is_subset = False
            grade_sizes_set = grade['sizes_set']
            
            # Check if this grade is a subset of any other grade
            for other_grade in grade_groups:
                if grade['product_key'] == other_grade['product_key']:
                    continue
                
                other_sizes_set = other_grade['sizes_set']
                
                # If all sizes in this grade are in another grade, it's a subset
                if grade_sizes_set.issubset(other_sizes_set):
                    is_subset = True
                    removed_count += 1
                    if removed_count <= 20:  # Show first 20 removals
                        print(f"  Removing: {grade['nom_marca']} {grade['des_cor']} "
                              f"({grade['sizes_count']} sizes: {grade['sizes_str'][:50]}...) - "
                              f"contained in {other_grade['nom_marca']} {other_grade['des_cor']} "
                              f"({other_grade['sizes_count']} sizes)")
                    break
            
            if not is_subset:
                filtered_grades.append(grade)
        
        print(f"\nRemoved {removed_count} subset grade groups")
        print(f"After filtering: {len(filtered_grades)} unique grade groups")
        print()
        
        # Group by size combination (same sizes = same grade group)
        # Multiple products can have the same size combination
        unique_grade_combinations = {}
        
        for grade in filtered_grades:
            sizes_key = grade['sizes_str']  # Use semicolon-separated string as key
            
            if sizes_key not in unique_grade_combinations:
                unique_grade_combinations[sizes_key] = {
                    'sizes': grade['sizes'],
                    'sizes_count': grade['sizes_count'],
                    'sizes_str': sizes_key,
                    'products': []
                }
            
            unique_grade_combinations[sizes_key]['products'].append({
                'nom_marca': grade['nom_marca'],
                'des_cor': grade['des_cor'],
                'product_key': grade['product_key']
            })
        
        # Convert to list and sort by size count
        final_grade_groups = list(unique_grade_combinations.values())
        final_grade_groups.sort(key=lambda x: x['sizes_count'], reverse=True)
        
        print(f"Unique size combinations: {len(final_grade_groups)}")
        print()
        
        # Print results
        print("=" * 80)
        print("UNIQUE GRADE GROUPS (based on actual product size combinations)")
        print("=" * 80)
        print()
        
        for i, grade in enumerate(final_grade_groups[:50], 1):  # Show first 50
            print(f"\n[GRADE {i}] {grade['sizes_count']} sizes")
            print(f"  Sizes: {grade['sizes_str']}")
            print(f"  Used by {len(grade['products'])} product(s)")
            if len(grade['products']) <= 5:
                for prod in grade['products']:
                    print(f"    - {prod['nom_marca']} {prod['des_cor']}")
            else:
                for prod in grade['products'][:3]:
                    print(f"    - {prod['nom_marca']} {prod['des_cor']}")
                print(f"    ... and {len(grade['products']) - 3} more")
        
        if len(final_grade_groups) > 50:
            print(f"\n... and {len(final_grade_groups) - 50} more grade groups")
        
        # Print summary statistics
        print()
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print()
        
        size_distribution = defaultdict(int)
        for grade in final_grade_groups:
            size_distribution[grade['sizes_count']] += 1
        
        print("Grade groups by size count:")
        for size_count in sorted(size_distribution.keys(), reverse=True):
            count = size_distribution[size_count]
            print(f"  {size_count} sizes: {count} grade group(s)")
        
        # Save to JSON
        output_file = project_root / 'product_grade_groups_extracted.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_unique_grade_groups': len(final_grade_groups),
                'total_products_analyzed': len(product_grades),
                'grade_groups': final_grade_groups,
                'formatted_for_levantamentos': [
                    {
                        'name': f"Grade Group {i+1} ({g['sizes_count']} sizes)",
                        'grade': [{'key': s, 'label': s} for s in g['sizes']],
                        'sizes_str': g['sizes_str']
                    }
                    for i, g in enumerate(final_grade_groups)
                ]
            }, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"[SUCCESS] Results saved to: {output_file}")
        print()
        
        # Print first few in copy-paste format
        print("=" * 80)
        print("FIRST 10 GRADE GROUPS (copy-paste format)")
        print("=" * 80)
        print()
        print("grades_options: [")
        for grade in final_grade_groups[:10]:
            sizes_formatted = ', '.join([f"{{key: '{s}', label: '{s}'}}" for s in grade['sizes']])
            print(f"  {{")
            print(f"    name: 'Grade Group ({grade['sizes_count']} sizes)',")
            print(f"    grade: [{sizes_formatted}]")
            print(f"  }},")
        print("  // ... and more")
        print("]")
        
        return final_grade_groups

if __name__ == '__main__':
    try:
        results = extract_product_grade_groups()
        print("\n[SUCCESS] Extraction complete!")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
