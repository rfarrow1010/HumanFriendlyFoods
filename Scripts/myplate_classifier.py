#!/usr/bin/env python3
"""
Add food group attributes and appropriate units to food database.

Food Groups:
- vegetables: Any vegetable or 100% vegetable juice (broccoli, carrots, spinach, etc.)
- fruits: Any fruit or 100% fruit juice (apple, banana, berries, etc.)
- grains: Foods made from wheat, rice, oats, cornmeal, barley or other cereal grains (bread, pasta, rice, oats, etc.)
- protein: Meat, poultry, seafood, eggs, beans, peas, lentils, nuts, seeds, soy products (chicken, fish, lentils, tofu, etc.)
- dairy: Milk, yogurt, cheese, and fortified soy beverages (milk, Greek yogurt, cheddar, etc.)
- fatsAndOils: Cooking oils, butter, and other fats (olive oil, coconut oil, butter, etc.)

All groups use grams (displayed as "units" where 1 unit = 100g).

Subgroups can be added later as needed for more detailed classification.

Fruits and vegetables need cup measurements added.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple


# Pattern-based classification rules
CLASSIFICATION_RULES = {
    'vegetables': {
        'name_patterns': [
            r'broccoli', r'cauliflower', r'carrot', r'celery', r'cucumber',
            r'lettuce', r'spinach', r'kale', r'cabbage', r'brussels sprout',
            r'asparagus', r'zucchini', r'squash', r'pumpkin', r'pepper', r'bell pepper',
            r'tomato', r'eggplant', r'onion', r'garlic', r'leek', r'mushroom',
            r'beet', r'radish', r'turnip', r'parsnip', r'chard', r'collard',
            r'arugula', r'bok choy', r'green bean', r'corn(?!meal|starch)',
            r'sweet potato', r'potato'
        ]
    },
    'fruits': {
        'name_patterns': [
            r'berry$', r'apple', r'banana', r'orange', r'grape', r'lemon', r'lime',
            r'peach', r'pear', r'plum', r'cherry', r'strawberr', r'blueberr',
            r'raspberr', r'blackberr', r'cranberr', r'mango', r'pineapple',
            r'watermelon', r'melon', r'kiwi', r'papaya', r'fig', r'date',
            r'apricot', r'nectarine', r'persimmon', r'pomegranate', r'guava',
            r'tangerine', r'grapefruit', r'cantaloupe'
        ]
    },
    'grains': {
        'name_patterns': [
            r'flour', r'bread', r'pasta', r'noodle', r'rice', r'oat', r'barley',
            r'quinoa', r'couscous', r'wheat', r'tortilla', r'cereal', r'cracker',
            r'bagel', r'muffin', r'pancake', r'waffle', r'cornmeal', r'bulgur',
            r'farro', r'millet', r'sorghum'
        ]
    },
    'protein': {
        'name_patterns': [
            # Meat, poultry, eggs
            r'chicken', r'beef', r'pork', r'turkey', r'duck', r'lamb', r'veal',
            r'egg', r'steak', r'ground', r'sausage', r'bacon', r'ham', r'loin',
            r'tenderloin', r'breast', r'thigh', r'broth',
            # Seafood
            r'fish', r'salmon', r'tuna', r'cod', r'tilapia', r'trout', r'halibut',
            r'sardine', r'mackerel', r'herring', r'anchovy', r'shrimp', r'crab',
            r'lobster', r'oyster', r'mussel', r'clam', r'scallop', r'squid',
            # Plant proteins
            r'tofu', r'tempeh', r'bean', r'lentil', r'pea(?!nut)', r'chickpea',
            r'nut', r'almond', r'cashew', r'walnut', r'peanut', r'pecan',
            r'pistachio', r'hazelnut', r'seed', r'chia', r'flax', r'hemp',
            r'sunflower seed', r'pumpkin seed', r'edamame', r'soy'
        ]
    },
    'dairy': {
        'name_patterns': [
            r'milk', r'cheese', r'yogurt', r'cream(?!.*cheese)', r'buttermilk',
            r'cottage cheese', r'mozzarella', r'cheddar', r'parmesan',
            r'ricotta', r'feta', r'gouda', r'swiss cheese', r'provolone',
            r'brie', r'camembert', r'blue cheese', r'gorgonzola', r'kefir',
            r'evaporated milk', r'condensed milk', r'half.?and.?half'
        ]
    },
    'fatsAndOils': {
        'name_patterns': [
            r'oil$', r'olive oil', r'coconut oil', r'vegetable oil', r'canola oil',
            r'avocado oil', r'sesame oil', r'peanut oil', r'sunflower oil',
            r'butter(?!milk|nut)', r'ghee', r'lard', r'shortening', r'margarine',
            r'mayo', r'mayonnaise'
        ]
    }
}


# Exclusion patterns (e.g., nut butter is protein, not dairy/fatsAndOils)
EXCLUSIONS = {
    'dairy': [r'butter.*nut', r'peanut butter', r'almond butter', r'coconut milk'],
    'fatsAndOils': [r'butter.*nut', r'peanut butter', r'almond butter']
}


def enrich_food_data(food_data: Dict) -> Dict:
    """
    Enrich a food data dictionary with food group classifications.
    This function can be called by import scripts to automatically classify foods.
    
    Args:
        food_data: Dictionary containing food data with at least a 'name' field
        
    Returns:
        Modified food_data dictionary with added attributes
    """
    food_name = food_data.get('name', '')
    if not food_name:
        return food_data
    
    existing_attributes = food_data.get('attributes', [])
    
    # Check if already has food group classification
    food_group_attributes = set(CLASSIFICATION_RULES.keys())
    if set(existing_attributes) & food_group_attributes:
        return food_data  # Already classified
    
    # Classify the food
    food_groups = classify_food(food_name, existing_attributes)
    
    if food_groups:
        # Add food group attributes
        if 'attributes' not in food_data:
            food_data['attributes'] = []
        
        for group in food_groups:
            if group not in food_data['attributes']:
                food_data['attributes'].append(group)
    
    return food_data


def classify_food(food_name: str, existing_attributes: List[str]) -> List[str]:
    """
    Classify a food into food groups based on its name.
    Returns list of food groups.
    
    Foods are classified into one primary group. Beans, peas, and lentils 
    are classified as protein (not vegetables).
    """
    food_name_lower = food_name.lower()
    food_groups = []
    
    for group, rules in CLASSIFICATION_RULES.items():
        # Check exclusions first
        if group in EXCLUSIONS:
            if any(re.search(pattern, food_name_lower) for pattern in EXCLUSIONS[group]):
                continue
        
        # Check if name matches any pattern
        for pattern in rules['name_patterns']:
            if re.search(pattern, food_name_lower):
                food_groups.append(group)
                break  # Found match for this group, stop checking patterns
    
    return food_groups


def analyze_foods(foods_dir: Path) -> Dict:
    """Analyze all foods and categorize them."""
    results = {
        'by_group': {group: [] for group in CLASSIFICATION_RULES.keys()},
        'uncategorized': [],
        'already_classified': []
    }
    
    food_group_attributes = set(CLASSIFICATION_RULES.keys())
    
    for filepath in sorted(foods_dir.glob('*.json')):
        try:
            with open(filepath, 'r') as f:
                food_data = json.load(f)
            
            food_name = food_data.get('name', filepath.stem)
            attributes = set(food_data.get('attributes', []))
            
            # Check if already has food group attribute
            if attributes & food_group_attributes:
                results['already_classified'].append({
                    'file': filepath.name,
                    'name': food_name,
                    'groups': list(attributes & food_group_attributes)
                })
                continue
            
            # Try to classify
            food_groups = classify_food(food_name, list(attributes))
            
            if food_groups:
                # Track by group
                for food_group in food_groups:
                    results['by_group'][food_group].append({
                        'file': filepath.name,
                        'name': food_name,
                        'all_groups': food_groups
                    })
            else:
                results['uncategorized'].append({
                    'file': filepath.name,
                    'name': food_name
                })
        
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
    
    return results


def print_analysis_report(results: Dict):
    """Print analysis report."""
    print("=" * 80)
    print("FOOD GROUP ANALYSIS")
    print("=" * 80)
    
    # Already categorized
    if results['already_classified']:
        print(f"\n✓ Already classified: {len(results['already_classified'])} files")
    
    # By group
    print("\n📊 SUGGESTED CLASSIFICATIONS")
    print("-" * 80)
    for group, foods in results['by_group'].items():
        if foods:
            print(f"\n{group.upper()} ({len(foods)} files):")
            for food in foods[:5]:  # Show first 5
                print(f"  - {food['name']} ({food['file']})")
            if len(foods) > 5:
                print(f"  ... and {len(foods) - 5} more")
    
    # Uncategorized
    if results['uncategorized']:
        print(f"\n❓ UNCATEGORIZED ({len(results['uncategorized'])} files)")
        print("-" * 80)
        print("These foods don't match automatic classification rules:")
        for item in results['uncategorized'][:10]:
            print(f"  - {item['name']} ({item['file']})")
        if len(results['uncategorized']) > 10:
            print(f"  ... and {len(results['uncategorized']) - 10} more")
    
    print("\n" + "=" * 80)


def apply_classifications(foods_dir: Path, dry_run: bool = True):
    """
    Apply food group classifications to foods.
    If dry_run is False, actually modifies the files.
    """
    results = analyze_foods(foods_dir)
    modifications = []
    
    # Process all classified foods
    processed_files = set()
    
    for food_group, foods in results['by_group'].items():
        for food_info in foods:
            filepath = foods_dir / food_info['file']
            
            # Skip if already processed
            if food_info['file'] in processed_files:
                continue
            processed_files.add(food_info['file'])
            
            with open(filepath, 'r') as f:
                food_data = json.load(f)
            
            modified = False
            added_groups = []
            
            # Add food group attributes
            attributes = food_data.get('attributes', [])
            for group in food_info['all_groups']:
                if group not in attributes:
                    attributes.append(group)
                    added_groups.append(group)
                    modified = True
            
            if modified:
                food_data['attributes'] = attributes
            
            if modified:
                modifications.append({
                    'file': food_info['file'],
                    'name': food_data['name'],
                    'groups': added_groups
                })
                
                if not dry_run:
                    with open(filepath, 'w') as f:
                        json.dump(food_data, f, indent=4)
    
    return modifications


def print_modification_report(modifications: List[Dict], dry_run: bool):
    """Print what would be/was modified."""
    if not modifications:
        print("\nNo modifications needed.")
        return
    
    print("\n" + "=" * 80)
    if dry_run:
        print("PROPOSED MODIFICATIONS (DRY RUN)")
    else:
        print("APPLIED MODIFICATIONS")
    print("=" * 80)
    
    print(f"\nTotal files to modify: {len(modifications)}\n")
    
    # Show first 20 modifications
    for mod in modifications[:20]:
        print(f"{mod['file']} - {mod['name']}")
        for group in mod['groups']:
            print(f"  + Add '{group}' attribute")
    
    if len(modifications) > 20:
        print(f"\n... and {len(modifications) - 20} more files")
    
    if dry_run:
        print("\n💡 Run with --apply to make these changes")
    else:
        print("\n✅ Changes applied successfully")
    
    print("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify foods into food groups')
    parser.add_argument('--foods-dir', type=Path, default=Path(__file__).parent.parent / 'Foods',
                       help='Path to Foods directory')
    parser.add_argument('--apply', action='store_true',
                       help='Apply changes to files (default is dry run)')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only show analysis, do not propose modifications')
    
    args = parser.parse_args()
    
    if not args.foods_dir.exists():
        print(f"Error: Foods directory not found at {args.foods_dir}")
        exit(1)
    
    if args.analyze_only:
        results = analyze_foods(args.foods_dir)
        print_analysis_report(results)
    else:
        modifications = apply_classifications(args.foods_dir, dry_run=not args.apply)
        print_modification_report(modifications, dry_run=not args.apply)
