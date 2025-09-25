#!/usr/bin/env python3
"""
Script to add dietary restriction attributes to all food JSON files.
"""

import json
import os
from pathlib import Path


# Define dietary restrictions and foods that violate them
DIETARY_RESTRICTIONS = {
    "vegetarian": {
        "exclude_names": [
            # Meat, poultry, fish
            "chicken", "beef", "pork", "bacon", "sausage", "turkey", "steak", 
            "salmon", "cod", "tuna", "shrimp", "fish"
        ],
        "exclude_keywords": ["meat", "poultry", "fish", "seafood"]
    },
    "vegan": {
        "exclude_names": [
            # All vegetarian exclusions plus dairy and eggs
            "chicken", "beef", "pork", "bacon", "sausage", "turkey", "steak",
            "salmon", "cod", "tuna", "shrimp", "fish",
            "milk", "cheese", "butter", "cream", "yogurt", "egg", "honey",
            "ghee", "buttermilk"
        ],
        "exclude_keywords": ["meat", "poultry", "fish", "seafood", "dairy", "milk", "cheese"]
    },
    "glutenFree": {
        "exclude_names": [
            "flour", "bread", "pasta", "couscous", "wheat", "barley", "rye",
            "breadcrumbs", "worcestershire"  # often contains wheat
        ],
        "exclude_keywords": ["wheat", "gluten", "flour", "bread"]
    },
    "lactoseIntolerant": {
        "exclude_names": [
            "milk", "cheese", "butter", "cream", "yogurt", "ghee", "buttermilk"
        ],
        "exclude_keywords": ["milk", "cheese", "dairy", "lactose"]
    },
    "nutFree": {
        "exclude_names": [
            "almonds", "walnuts", "pecans", "cashews", "peanuts", "peanut",
            "almond", "tahini"  # sesame seed paste, but often grouped with tree nuts
        ],
        "exclude_keywords": ["nut", "almond", "walnut", "pecan", "cashew", "peanut"]
    },
    "soyFree": {
        "exclude_names": [
            "tofu", "tempeh", "soy", "tamari", "miso", "edamame"
        ],
        "exclude_keywords": ["soy", "tofu", "tempeh"]
    },
    "eggFree": {
        "exclude_names": ["egg"],
        "exclude_keywords": ["egg"]
    },
    "halal": {
        "exclude_names": [
            # Pork products - definitively not halal
            "pork", "bacon", "ham"
        ],
        "exclude_keywords": ["pork"]
        # Note: We're being conservative - chicken, beef etc. could be halal if prepared properly
        # but we can't assume preparation method, so we don't exclude them
    },
    "kosher": {
        "exclude_names": [
            # Pork and shellfish - definitively not kosher
            "pork", "bacon", "ham", "shrimp", "shellfish"
        ],
        "exclude_keywords": ["pork", "shellfish"]
        # Note: Similar to halal, being conservative about preparation
    }
}


def food_violates_restriction(food_name: str, restriction_name: str) -> bool:
    """
    Check if a food violates a dietary restriction based on its name.
    
    Args:
        food_name: The name of the food (lowercase)
        restriction_name: The name of the dietary restriction
    
    Returns:
        True if the food violates the restriction, False otherwise
    """
    restriction = DIETARY_RESTRICTIONS[restriction_name]
    
    # Check exact name matches
    for excluded_name in restriction["exclude_names"]:
        if excluded_name.lower() in food_name.lower():
            return True
    
    # Check keyword matches
    for keyword in restriction["exclude_keywords"]:
        if keyword.lower() in food_name.lower():
            return True
    
    return False


def get_dietary_attributes(food_name: str) -> list:
    """
    Get the list of dietary restriction attributes that apply to a food.
    
    Args:
        food_name: The name of the food
    
    Returns:
        List of dietary restriction attributes that the food satisfies
    """
    attributes = []
    
    for restriction in DIETARY_RESTRICTIONS.keys():
        if not food_violates_restriction(food_name, restriction):
            attributes.append(restriction)
    
    return attributes


def update_food_json(file_path: Path) -> bool:
    """
    Update a food JSON file with dietary restriction attributes.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        True if the file was updated, False if there was an error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            food_data = json.load(f)
        
        # Get the food name
        food_name = food_data.get("name", "")
        
        # Get existing attributes (preserve existing ones)
        existing_attributes = food_data.get("attributes", [])
        
        # Get dietary attributes
        dietary_attributes = get_dietary_attributes(food_name)
        
        # Combine existing attributes with new dietary attributes
        # Remove duplicates while preserving order
        all_attributes = existing_attributes.copy()
        for attr in dietary_attributes:
            if attr not in all_attributes:
                all_attributes.append(attr)
        
        # Update the attributes
        food_data["attributes"] = all_attributes
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(food_data, f, ensure_ascii=False, indent=4)
        
        print(f"Updated {file_path.name}: {food_name} -> {dietary_attributes}")
        return True
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def main():
    """Main function to process all food JSON files."""
    # Get the Foods directory
    foods_dir = Path(__file__).parent.parent / "Foods"
    
    if not foods_dir.exists():
        print(f"Foods directory not found: {foods_dir}")
        return
    
    # Get all JSON files
    json_files = list(foods_dir.glob("*.json"))
    
    if not json_files:
        print("No JSON files found in Foods directory")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    successful = 0
    failed = 0
    
    # Process each file
    for json_file in sorted(json_files):
        if update_food_json(json_file):
            successful += 1
        else:
            failed += 1
    
    print(f"\nProcessing complete:")
    print(f"Successfully updated: {successful}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()