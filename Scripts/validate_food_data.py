#!/usr/bin/env python3
"""
Validate food database entries for data quality issues.

This script identifies:
1. Nutrients with missing units
2. Foods with suspiciously many zero values
3. Foods with incomplete data
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple


def load_food_file(filepath: Path) -> Dict:
    """Load a food JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def check_missing_units(food_data: Dict, filepath: Path) -> List[str]:
    """Check for nutrients with missing units."""
    issues = []
    
    for nutrient in food_data.get('nutrients', []):
        if nutrient.get('unit', '') == '' and nutrient.get('amountPer100g', 0) != 0:
            issues.append(f"  - {nutrient['name']}: has value {nutrient['amountPer100g']} but missing unit")
    
    return issues


def check_zero_values(food_data: Dict, filepath: Path) -> Tuple[int, int, List[str]]:
    """Check for suspicious patterns of zero values."""
    nutrients = food_data.get('nutrients', [])
    total_nutrients = len(nutrients)
    zero_count = sum(1 for n in nutrients if n.get('amountPer100g', 0) == 0.0)
    
    # Common nutrients that should rarely be zero in real foods
    important_nutrients = ['calories', 'protein', 'fat', 'carbohydrates']
    zero_important = [n['name'] for n in nutrients 
                     if n['name'] in important_nutrients and n.get('amountPer100g', 0) == 0.0]
    
    return zero_count, total_nutrients, zero_important


def check_missing_unit_options(food_data: Dict, filepath: Path) -> List[str]:
    """Check if food has adequate unit options."""
    issues = []
    unit_options = food_data.get('unitOptions', [])
    
    if len(unit_options) == 0:
        issues.append("  - No unit options defined")
    elif len(unit_options) == 1 and unit_options[0]['unitAbbreviation'] == 'g':
        issues.append("  - Only has gram units (consider adding practical serving sizes)")
    
    return issues


def validate_all_foods(foods_dir: Path, verbose: bool = False) -> Dict:
    """Validate all food files in the directory."""
    results = {
        'missing_units': [],
        'high_zero_percentage': [],
        'zero_macros': [],
        'limited_units': [],
        'total_files': 0
    }
    
    json_files = sorted(foods_dir.glob('*.json'))
    results['total_files'] = len(json_files)
    
    for filepath in json_files:
        try:
            food_data = load_food_file(filepath)
            food_name = food_data.get('name', filepath.stem)
            has_issues = False
            
            # Check for missing units
            missing_unit_issues = check_missing_units(food_data, filepath)
            if missing_unit_issues:
                results['missing_units'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'issues': missing_unit_issues
                })
                has_issues = True
            
            # Check for zero values
            zero_count, total_count, zero_important = check_zero_values(food_data, filepath)
            zero_percentage = (zero_count / total_count * 100) if total_count > 0 else 0
            
            if zero_percentage > 70:  # More than 70% zeros
                results['high_zero_percentage'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'zero_count': zero_count,
                    'total_count': total_count,
                    'percentage': round(zero_percentage, 1)
                })
                has_issues = True
            
            if zero_important:
                results['zero_macros'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'zero_nutrients': zero_important
                })
                has_issues = True
            
            # Check unit options
            unit_issues = check_missing_unit_options(food_data, filepath)
            if unit_issues and verbose:
                results['limited_units'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'issues': unit_issues
                })
            
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
    
    return results


def print_report(results: Dict):
    """Print a formatted validation report."""
    print("=" * 80)
    print("FOOD DATABASE VALIDATION REPORT")
    print("=" * 80)
    print(f"\nTotal files scanned: {results['total_files']}\n")
    
    # Missing units
    if results['missing_units']:
        print(f"\n⚠️  MISSING UNITS ({len(results['missing_units'])} files)")
        print("-" * 80)
        for item in results['missing_units']:
            print(f"\n{item['file']} - {item['name']}")
            for issue in item['issues']:
                print(issue)
    else:
        print("\n✓ No missing unit issues found")
    
    # High zero percentage
    if results['high_zero_percentage']:
        print(f"\n⚠️  HIGH ZERO PERCENTAGE ({len(results['high_zero_percentage'])} files)")
        print("-" * 80)
        for item in results['high_zero_percentage']:
            print(f"\n{item['file']} - {item['name']}")
            print(f"  - {item['zero_count']}/{item['total_count']} nutrients are zero ({item['percentage']}%)")
    else:
        print("\n✓ No excessive zero values found")
    
    # Zero macros
    if results['zero_macros']:
        print(f"\n⚠️  ZERO MACRONUTRIENTS ({len(results['zero_macros'])} files)")
        print("-" * 80)
        for item in results['zero_macros']:
            print(f"\n{item['file']} - {item['name']}")
            print(f"  - Zero values for: {', '.join(item['zero_nutrients'])}")
    else:
        print("\n✓ No zero macronutrient issues found")
    
    # Limited units (if verbose)
    if results['limited_units']:
        print(f"\n💡 LIMITED UNIT OPTIONS ({len(results['limited_units'])} files)")
        print("-" * 80)
        for item in results['limited_units'][:10]:  # Show first 10
            print(f"\n{item['file']} - {item['name']}")
            for issue in item['issues']:
                print(issue)
        if len(results['limited_units']) > 10:
            print(f"\n... and {len(results['limited_units']) - 10} more")
    
    print("\n" + "=" * 80)


def export_issues_json(results: Dict, output_path: Path):
    """Export issues to a JSON file for programmatic processing."""
    issues = {
        'missing_units': results['missing_units'],
        'high_zero_percentage': results['high_zero_percentage'],
        'zero_macros': results['zero_macros']
    }
    
    with open(output_path, 'w') as f:
        json.dump(issues, f, indent=2)
    
    print(f"\n📄 Issues exported to: {output_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate food database entries')
    parser.add_argument('--foods-dir', type=Path, default=Path(__file__).parent.parent / 'Foods',
                       help='Path to Foods directory')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show additional warnings like limited unit options')
    parser.add_argument('--export', type=Path,
                       help='Export issues to JSON file')
    
    args = parser.parse_args()
    
    if not args.foods_dir.exists():
        print(f"Error: Foods directory not found at {args.foods_dir}")
        exit(1)
    
    results = validate_all_foods(args.foods_dir, verbose=args.verbose)
    print_report(results)
    
    if args.export:
        export_issues_json(results, args.export)
