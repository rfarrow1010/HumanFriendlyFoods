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


def check_required_macros(food_data: Dict, filepath: Path) -> List[str]:
    """
    Check for required macronutrients that MUST have values.
    
    This is a critical validation - foods with missing macros should NOT be merged.
    
    Rules:
    1. Calories must NEVER be zero or missing (except for zero-calorie items like water/baking soda)
    2. At least ONE macro (protein, fat, or carbs) must be non-zero
    3. All three macros (protein, fat, carbs) must be present (but can be zero)
    
    This allows for legitimate cases like:
    - Oils: fat=high, protein=0, carbs=0
    - Meats: protein=high, fat=varies, carbs=0
    - Sugar: carbs=high, protein=0, fat=0
    """
    # Hard-coded exceptions for legitimate zero-calorie items
    ZERO_CALORIE_EXCEPTIONS = ['Salt.json', 'BakingSoda.json', 'TapWater.json']
    
    required_macros = ['calories', 'protein', 'fat', 'carbohydrates']
    nutrients = food_data.get('nutrients', [])
    nutrient_dict = {n['name']: n.get('amountPer100g', 0) for n in nutrients}
    
    issues = []
    
    # Check if any macros are completely missing from the data
    for macro in required_macros:
        if macro not in nutrient_dict:
            issues.append(f"{macro} (MISSING from data)")
    
    # If any are missing, return early
    if issues:
        return issues
    
    # Check if calories are zero (unless it's a zero-calorie exception)
    if nutrient_dict['calories'] == 0.0 and filepath.name not in ZERO_CALORIE_EXCEPTIONS:
        issues.append("calories (ZERO - must have calorie value)")
    
    # Check if ALL three macros are zero (protein, fat, carbs)
    # This would be suspicious unless calories are also zero (like baking soda/water)
    protein_zero = nutrient_dict['protein'] == 0.0
    fat_zero = nutrient_dict['fat'] == 0.0
    carbs_zero = nutrient_dict['carbohydrates'] == 0.0
    
    if protein_zero and fat_zero and carbs_zero:
        # Only flag if calories are also zero or if this seems like a real food
        if nutrient_dict['calories'] > 0:
            issues.append("ALL macros are zero (protein, fat, carbs) but calories is non-zero - data inconsistency")
    
    return issues


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
        'missing_required_macros': [],  # New critical validation
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
            
            # CRITICAL: Check for missing or zero required macros (blocks merge)
            missing_macros = check_required_macros(food_data, filepath)
            if missing_macros:
                results['missing_required_macros'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'missing_macros': missing_macros
                })
                has_issues = True
            
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
            
            # Legacy check - keeping for backward compatibility
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
    
    # CRITICAL: Missing required macros (blocks merge)
    if results['missing_required_macros']:
        print(f"\n🚫 CRITICAL: MISSING REQUIRED MACROS ({len(results['missing_required_macros'])} files)")
        print("=" * 80)
        print("These foods are MISSING required macronutrients and MUST be fixed before merge!")
        print("Required macros: calories, protein, fat, carbohydrates")
        print("-" * 80)
        for item in results['missing_required_macros']:
            print(f"\n{item['file']} - {item['name']}")
            print(f"  - Missing/Zero: {', '.join(item['missing_macros'])}")
    else:
        print("\n✓ All foods have required macronutrients (calories, protein, fat, carbohydrates)")
    
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
    
    # Zero macros (legacy check)
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
        'missing_required_macros': results['missing_required_macros'],  # Critical blocker
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
