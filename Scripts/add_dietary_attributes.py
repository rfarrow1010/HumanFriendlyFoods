#!/usr/bin/env python3
"""
Script to add dietary restriction attributes to all food JSON files.
"""

import json
import os
from pathlib import Path


# Define special cases that need custom handling
SPECIAL_CASES = {
    # Plant-based "butter" products - these are vegan despite having "butter" in name
    "plant_based_butters": {
        "names": ["almond butter", "peanut butter", "cashew butter", "sunflower butter"],
        "add_attributes": ["vegan", "lactoseIntolerant"]
    },
    # Coconut products - these are nut-free despite "coconut" containing "nut"
    "coconut_products": {
        "names": ["coconut milk", "canned coconut milk", "coconut oil"],
        "add_attributes": ["vegan", "lactoseIntolerant", "nutFree"],
        "remove_attributes": []
    },
    # Other plant-based "milk" products - these are vegan but may not be nut-free
    "other_plant_milks": {
        "names": ["almond milk", "soy milk", "oat milk", "rice milk"],
        "add_attributes": ["vegan", "lactoseIntolerant"],
        "remove_attributes": []
    },
    # Products that contain eggs
    "egg_containing": {
        "names": ["mayonnaise"],
        "remove_attributes": ["vegan", "eggFree"]
    },
    # Sausages that likely contain pork
    "pork_sausages": {
        "names": ["italian sausage", "polish sausage", "bratwurst"],
        "remove_attributes": ["halal", "kosher"]
    }
}


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
        "exclude_keywords": ["meat", "poultry", "fish", "seafood", "dairy", "cheese"],
        # Special handling: exclude items with "milk" or "butter" UNLESS they're plant-based
        "exclude_keywords_with_exceptions": {
            "milk": ["coconut milk", "almond milk", "soy milk", "oat milk", "rice milk", "canned coconut milk"],
            "butter": ["almond butter", "peanut butter", "cashew butter", "sunflower butter"]
        }
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
        "exclude_keywords": ["cheese", "dairy", "lactose"],
        # Special handling: exclude items with "milk" or "butter" UNLESS they're plant-based
        "exclude_keywords_with_exceptions": {
            "milk": ["coconut milk", "almond milk", "soy milk", "oat milk", "rice milk", "canned coconut milk"],
            "butter": ["almond butter", "peanut butter", "cashew butter", "sunflower butter"]
        }
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
        "exclude_names": ["egg", "mayonnaise"],
        "exclude_keywords": ["egg"]
    },
    "halal": {
        "exclude_names": [
            # Pork products - definitively not halal
            "pork", "bacon", "ham", "italian sausage", "polish sausage"
        ],
        "exclude_keywords": ["pork"]
        # Note: We're being conservative - chicken, beef etc. could be halal if prepared properly
        # but we can't assume preparation method, so we don't exclude them
    },
    "kosher": {
        "exclude_names": [
            # Pork and shellfish - definitively not kosher
            "pork", "bacon", "ham", "shrimp", "shellfish", "italian sausage", "polish sausage"
        ],
        "exclude_keywords": ["pork", "shellfish"]
        # Note: Assuming user will buy kosher-certified products when needed
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
    food_name_lower = food_name.lower()
    
    # Check exact name matches
    for excluded_name in restriction.get("exclude_names", []):
        if excluded_name.lower() in food_name_lower:
            return True
    
    # Check keyword matches with exceptions
    if "exclude_keywords_with_exceptions" in restriction:
        for keyword, exceptions in restriction["exclude_keywords_with_exceptions"].items():
            if keyword.lower() in food_name_lower:
                # Check if this food is in the exception list
                is_exception = any(exc.lower() == food_name_lower for exc in exceptions)
                if not is_exception:
                    return True
    
    # Check regular keyword matches
    for keyword in restriction.get("exclude_keywords", []):
        if keyword.lower() in food_name_lower:
            return True
    
    return False


def apply_special_cases(food_name: str, attributes: list) -> list:
    """
    Apply special case rules to modify attributes for specific foods.
    
    Args:
        food_name: The name of the food
        attributes: Current list of attributes
    
    Returns:
        Modified list of attributes
    """
    food_name_lower = food_name.lower()
    modified_attributes = attributes.copy()
    
    for case_name, case_rules in SPECIAL_CASES.items():
        # Check if this food matches any of the special case names
        for special_name in case_rules["names"]:
            if special_name.lower() == food_name_lower:
                # Add specified attributes
                if "add_attributes" in case_rules:
                    for attr in case_rules["add_attributes"]:
                        if attr not in modified_attributes:
                            modified_attributes.append(attr)
                
                # Remove specified attributes
                if "remove_attributes" in case_rules:
                    for attr in case_rules["remove_attributes"]:
                        if attr in modified_attributes:
                            modified_attributes.remove(attr)
                
                break  # Found a match, no need to check other names in this case
    
    return modified_attributes


def get_dietary_attributes(food_name: str) -> list:
    """
    Get the list of dietary restriction attributes that apply to a food.
    
    Args:
        food_name: The name of the food
    
    Returns:
        List of dietary restriction attributes that the food satisfies
    """
    attributes = []
    
    # First, apply standard restriction logic
    for restriction in DIETARY_RESTRICTIONS.keys():
        if not food_violates_restriction(food_name, restriction):
            attributes.append(restriction)
    
    # Then apply special case modifications
    attributes = apply_special_cases(food_name, attributes)
    
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
        
        # Get dietary attributes (replaces existing dietary attributes completely)
        dietary_attributes = get_dietary_attributes(food_name)
        
        # Filter existing attributes to keep only non-dietary ones
        dietary_restriction_names = set(DIETARY_RESTRICTIONS.keys())
        non_dietary_attributes = [attr for attr in existing_attributes if attr not in dietary_restriction_names]
        
        # Combine non-dietary attributes with new dietary attributes
        all_attributes = non_dietary_attributes + dietary_attributes
        
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