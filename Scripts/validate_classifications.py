#!/usr/bin/env python3
"""
Validate that all foods have food group classifications.

This script checks that every food in the database has at least one
MyPlate food group classification from:
- vegetables
- fruits
- grains
- protein
- dairy
- fatsAndOils
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


FOOD_GROUPS = {'vegetables', 'fruits', 'grains', 'protein', 'dairy', 'fatsAndOils'}


def load_food_file(filepath: Path) -> Dict:
    """Load a food JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def validate_classifications(foods_dir: Path) -> Dict:
    """Validate all foods have at least one food group classification."""
    results = {
        'unclassified': [],
        'classified': [],
        'total_foods': 0
    }
    
    json_files = sorted(foods_dir.glob('*.json'))
    results['total_foods'] = len(json_files)
    
    for filepath in json_files:
        try:
            food_data = load_food_file(filepath)
            food_name = food_data.get('name', filepath.stem)
            attributes = set(food_data.get('attributes', []))
            
            # Check if food has at least one food group classification
            if attributes & FOOD_GROUPS:
                results['classified'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'groups': list(attributes & FOOD_GROUPS)
                })
            else:
                results['unclassified'].append({
                    'file': filepath.name,
                    'name': food_name
                })
                
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}", file=sys.stderr)
            sys.exit(1)
    
    return results


def print_report(results: Dict):
    """Print a formatted validation report."""
    print("=" * 80)
    print("FOOD GROUP CLASSIFICATION VALIDATION")
    print("=" * 80)
    print(f"\nTotal foods: {results['total_foods']}")
    print(f"Classified: {len(results['classified'])}")
    print(f"Unclassified: {len(results['unclassified'])}")
    
    if results['unclassified']:
        print(f"\n❌ UNCLASSIFIED FOODS:")
        print("-" * 80)
        for item in results['unclassified'][:20]:
            print(f"  - {item['name']} ({item['file']})")
        
        if len(results['unclassified']) > 20:
            print(f"  ... and {len(results['unclassified']) - 20} more")
        
        print(f"\n💡 To fix: Run 'python3 Scripts/myplate_classifier.py --apply'")
    else:
        print(f"\n✅ All foods have food group classifications!")
    
    print("=" * 80)


def export_issues_json(results: Dict, output_path: Path):
    """Export unclassified foods to a JSON file."""
    issues = {
        'unclassified': results['unclassified'],
        'total_foods': results['total_foods'],
        'total_classified': len(results['classified']),
        'total_unclassified': len(results['unclassified'])
    }
    
    with open(output_path, 'w') as f:
        json.dump(issues, f, indent=2)
    
    print(f"\n📄 Issues exported to: {output_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate that all foods have food group classifications'
    )
    parser.add_argument(
        '--foods-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'Foods',
        help='Path to Foods directory'
    )
    parser.add_argument(
        '--export',
        type=Path,
        help='Export issues to JSON file'
    )
    
    args = parser.parse_args()
    
    if not args.foods_dir.exists():
        print(f"Error: Foods directory not found at {args.foods_dir}", file=sys.stderr)
        sys.exit(1)
    
    results = validate_classifications(args.foods_dir)
    print_report(results)
    
    if args.export:
        export_issues_json(results, args.export)
    
    # Exit with error code if there are unclassified foods
    if results['unclassified']:
        sys.exit(1)
    else:
        sys.exit(0)
