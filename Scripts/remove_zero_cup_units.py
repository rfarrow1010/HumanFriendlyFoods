#!/usr/bin/env python3
"""Remove cup units with portionInGrams=0.0 from all food files."""

import json
import glob
from pathlib import Path

def main():
    foods_dir = Path(__file__).parent.parent / 'Foods'
    foods_modified = []

    for filepath in sorted(foods_dir.glob('*.json')):
        try:
            with open(filepath, 'r') as f:
                food_data = json.load(f)
            
            unit_options = food_data.get('unitOptions', [])
            original_count = len(unit_options)
            
            # Remove cup units with portionInGrams = 0.0
            filtered_units = [
                unit for unit in unit_options 
                if not (unit.get('unitAbbreviation') in ['cup', 'c'] and unit.get('portionInGrams', -1) == 0.0)
            ]
            
            if len(filtered_units) < original_count:
                food_data['unitOptions'] = filtered_units
                
                with open(filepath, 'w') as f:
                    json.dump(food_data, f, indent=4)
                
                foods_modified.append({
                    'file': filepath.name,
                    'name': food_data.get('name', 'Unknown'),
                    'removed': original_count - len(filtered_units)
                })
        
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")

    print(f"\n{'='*80}")
    print(f"REMOVED CUP UNITS WITH portionInGrams=0.0")
    print(f"{'='*80}\n")
    print(f"Total foods modified: {len(foods_modified)}\n")

    if foods_modified:
        for item in foods_modified[:30]:
            print(f"✓ {item['name']} ({item['file']}) - removed {item['removed']} unit(s)")
        
        if len(foods_modified) > 30:
            print(f"\n... and {len(foods_modified) - 30} more")
    else:
        print("No foods needed modification")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
