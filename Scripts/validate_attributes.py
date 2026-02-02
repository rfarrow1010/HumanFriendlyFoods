#!/usr/bin/env python3
"""
Validate that all attribute strings in food JSON files match valid Swift FoodAttribute enum cases.

This ensures compatibility with Swift's Codable protocol.
"""

import json
from pathlib import Path
from typing import Set, List, Dict


# Valid attribute values that map to Swift FoodAttribute enum cases
VALID_ATTRIBUTES = {
    # Dietary restrictions/preferences
    'vegetarian',
    'vegan',
    'glutenFree',
    'lactoseIntolerant',
    'nutFree',
    'soyFree',
    'eggFree',
    'halal',
    'kosher',
    
    # MyPlate Food Groups
    'fruit',
    'vegetable',
    'grain',
    'animalProtein',  # Swift splits "protein" into three categories
    'seafood',
    'plantProtein',
    'dairy',
    'oil',  # Additional category for oils
    
    # Fruit Subgroups
    'wholeFruit',
    'fruitJuice',
    
    # Vegetable Subgroups
    'darkGreenVegetable',
    'redOrangeVegetable',
    'beansPeasLentils',
    'starchyVegetable',
    'otherVegetable',
    
    # Grain Subgroups
    'wholeGrain',
    'refinedGrain',
    
    # Protein Subgroups
    'meatPoultryEggs',
    'nutsSeedsSoy',
    # seafood is defined above as main group
    # beansPeasLentils defined above (shared)
    
    # Dairy Subgroups
    'milk',
    'yogurt',
    'cheese',
    
    # Legacy/other
    'foundation',  # annotation, not attribute, but sometimes in attributes
}


def validate_food_file(filepath: Path) -> List[str]:
    """Validate attributes in a single food file."""
    issues = []
    
    try:
        with open(filepath, 'r') as f:
            food_data = json.load(f)
        
        attributes = food_data.get('attributes', [])
        
        for attr in attributes:
            if attr not in VALID_ATTRIBUTES:
                issues.append(f"Invalid attribute: '{attr}'")
        
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues


def validate_all_foods(foods_dir: Path) -> Dict:
    """Validate all food files."""
    results = {
        'valid_files': [],
        'invalid_files': [],
        'total_files': 0,
        'unknown_attributes': set()
    }
    
    json_files = sorted(foods_dir.glob('*.json'))
    results['total_files'] = len(json_files)
    
    for filepath in json_files:
        issues = validate_food_file(filepath)
        
        if issues:
            results['invalid_files'].append({
                'file': filepath.name,
                'name': json.load(open(filepath)).get('name', filepath.stem),
                'issues': issues
            })
            
            # Track unique unknown attributes
            for issue in issues:
                if issue.startswith("Invalid attribute:"):
                    attr = issue.split("'")[1]
                    results['unknown_attributes'].add(attr)
        else:
            results['valid_files'].append(filepath.name)
    
    return results


def print_report(results: Dict):
    """Print validation report."""
    print("=" * 80)
    print("ATTRIBUTE VALIDATION REPORT (Swift Codable Compatibility)")
    print("=" * 80)
    print(f"\nTotal files: {results['total_files']}")
    print(f"Valid files: {len(results['valid_files'])}")
    print(f"Invalid files: {len(results['invalid_files'])}")
    
    if results['unknown_attributes']:
        print(f"\n⚠️  UNKNOWN ATTRIBUTES FOUND")
        print("-" * 80)
        print("These attributes don't match any Swift FoodAttribute enum case:")
        for attr in sorted(results['unknown_attributes']):
            print(f"  - '{attr}'")
        print("\nThese need to either:")
        print("  1. Be added to the Swift FoodAttribute enum")
        print("  2. Be removed from the JSON files")
        print("  3. Be corrected if they're typos")
    
    if results['invalid_files']:
        print(f"\n⚠️  FILES WITH INVALID ATTRIBUTES")
        print("-" * 80)
        for item in results['invalid_files'][:20]:
            print(f"\n{item['file']} - {item['name']}")
            for issue in item['issues']:
                print(f"  {issue}")
        
        if len(results['invalid_files']) > 20:
            print(f"\n... and {len(results['invalid_files']) - 20} more files")
    else:
        print("\n✅ All attributes are valid!")
        print("All JSON files are compatible with Swift Codable decoding.")
    
    print("\n" + "=" * 80)


def generate_swift_enum():
    """Generate Swift enum code from valid attributes."""
    print("\n" + "=" * 80)
    print("SWIFT ENUM CODE")
    print("=" * 80)
    print("\nenum FoodAttribute: String, Codable, Hashable, CaseIterable {")
    
    categories = {
        'Dietary': ['vegetarian', 'vegan', 'glutenFree', 'lactoseIntolerant', 
                   'nutFree', 'soyFree', 'eggFree', 'halal', 'kosher'],
        'Food Groups': ['fruit', 'vegetable', 'grain', 'animalProtein', 'seafood', 
                       'plantProtein', 'dairy', 'oil'],
        'Fruit Subgroups': ['wholeFruit', 'fruitJuice'],
        'Vegetable Subgroups': ['darkGreenVegetable', 'redOrangeVegetable', 
                                'beansPeasLentils', 'starchyVegetable', 'otherVegetable'],
        'Grain Subgroups': ['wholeGrain', 'refinedGrain'],
        'Protein Subgroups': ['meatPoultryEggs', 'nutsSeedsSoy'],
        'Dairy Subgroups': ['milk', 'yogurt', 'cheese'],
    }
    
    for category, attrs in categories.items():
        print(f"    // {category}")
        for attr in attrs:
            print(f"    case {attr}")
        print()
    
    print("}")
    print("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate attributes for Swift Codable compatibility'
    )
    parser.add_argument('--foods-dir', type=Path, 
                       default=Path(__file__).parent.parent / 'Foods',
                       help='Path to Foods directory')
    parser.add_argument('--generate-swift', action='store_true',
                       help='Generate Swift enum code')
    
    args = parser.parse_args()
    
    if not args.foods_dir.exists():
        print(f"Error: Foods directory not found at {args.foods_dir}")
        exit(1)
    
    results = validate_all_foods(args.foods_dir)
    print_report(results)
    
    if args.generate_swift:
        generate_swift_enum()
    
    # Exit with error code if validation failed
    if results['invalid_files']:
        exit(1)
