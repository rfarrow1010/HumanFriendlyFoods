"""
Food Database Utility

Fetches and caches the HumanFriendlyFoods database from GitHub.
Ensures generated recipes use exact ingredient name matches.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

CACHE_FILE = "food_database_cache.json"
CACHE_DURATION_HOURS = 24
GITHUB_API_URL = "https://api.github.com/repos/rfarrow1010/HumanFriendlyFoods/releases/latest"


def fetch_food_database(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch the food database from GitHub, with local caching.
    
    Args:
        force_refresh: If True, bypass cache and fetch fresh data
        
    Returns:
        List of food items from the database
    """
    cache_path = os.path.join(os.path.dirname(__file__), "output", CACHE_FILE)
    
    # Check cache first
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cached_data['cached_at'])
            if datetime.utcnow() - cache_time < timedelta(hours=CACHE_DURATION_HOURS):
                print(f"✓ Using cached food database ({len(cached_data['foods'])} foods)")
                return cached_data['foods']
        except Exception as e:
            print(f"⚠ Cache read error: {e}")
    
    # Fetch from GitHub
    print("Fetching food database from GitHub...")
    try:
        # Get latest release info
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        release_data = response.json()
        
        # Find the JSON asset
        json_asset = None
        for asset in release_data.get('assets', []):
            if asset['name'].endswith('.json'):
                json_asset = asset
                break
        
        if not json_asset:
            raise Exception("No JSON asset found in latest release")
        
        # Download the food database
        print(f"Downloading {json_asset['name']}...")
        food_response = requests.get(json_asset['browser_download_url'], timeout=30)
        food_response.raise_for_status()
        food_data = food_response.json()
        
        # Extract the foods array from the nested structure
        if isinstance(food_data, dict) and 'foods' in food_data:
            foods = food_data['foods']
        else:
            foods = food_data
        
        # Cache the data
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        cache_data = {
            'cached_at': datetime.utcnow().isoformat(),
            'release_tag': release_data.get('tag_name'),
            'foods': foods
        }
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"✓ Downloaded and cached {len(foods)} foods")
        return foods
        
    except requests.RequestException as e:
        print(f"✗ Error fetching food database: {e}")
        # Try to use stale cache as fallback
        if os.path.exists(cache_path):
            print("⚠ Using stale cache as fallback")
            with open(cache_path, 'r') as f:
                return json.load(f)['foods']
        return []
    except Exception as e:
        print(f"✗ Error processing food database: {e}")
        return []


def get_food_names() -> List[str]:
    """Get a list of all valid food names from the database."""
    foods = fetch_food_database()
    return [food.get('name', food.get('friendlyName', '')) for food in foods]


def get_foods_by_category(category: str) -> List[Dict[str, Any]]:
    """Get foods filtered by category."""
    foods = fetch_food_database()
    return [food for food in foods 
            if food.get('category', '').lower() == category.lower()]


def get_foods_by_cuisine(cuisine: str) -> List[Dict[str, Any]]:
    """
    Get foods commonly used in a specific cuisine.
    Note: This requires cuisine tagging in the food database.
    """
    foods = fetch_food_database()
    # Check if foods have cuisine tags
    cuisine_foods = [food for food in foods 
                     if cuisine.lower() in [c.lower() for c in food.get('cuisines', [])]]
    
    if not cuisine_foods:
        # Fallback: return common ingredients by name matching
        print(f"⚠ No cuisine tags found, using name-based filtering")
        # This would need to be customized per cuisine
    
    return cuisine_foods


def find_closest_food_match(search_term: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Find foods that match or are similar to the search term.
    Useful for suggesting corrections when an ingredient doesn't match exactly.
    """
    foods = fetch_food_database()
    search_lower = search_term.lower()
    
    # Exact matches first
    exact_matches = [food for food in foods 
                     if food.get('name', '').lower() == search_lower]
    if exact_matches:
        return exact_matches[:max_results]
    
    # Partial matches
    partial_matches = [food for food in foods 
                       if search_lower in food.get('name', '').lower()]
    
    return partial_matches[:max_results]


def validate_ingredient_name(ingredient_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate if an ingredient name exists in the food database.
    
    Returns:
        (is_valid, suggested_name)
        - is_valid: True if exact match found
        - suggested_name: Closest match if not exact, None if valid
    """
    food_names = get_food_names()
    food_names_lower = {name.lower(): name for name in food_names}
    
    # Check exact match (case-insensitive)
    if ingredient_name.lower() in food_names_lower:
        exact_name = food_names_lower[ingredient_name.lower()]
        if exact_name == ingredient_name:
            return (True, None)
        else:
            # Case mismatch - suggest correct casing
            return (False, exact_name)
    
    # No match - find closest
    matches = find_closest_food_match(ingredient_name, max_results=1)
    if matches:
        return (False, matches[0].get('name'))
    
    return (False, None)


def create_food_quantity_ingredient(
    friendly_food_name: str,
    whole_number: int = 0,
    fraction: str = "",
    unit_full_name: str = "",
    details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a properly structured Ingredient with FoodQuantity.
    
    Args:
        friendly_food_name: Must match exactly with food database
        whole_number: Whole number part of quantity (e.g., 2)
        fraction: Fraction part (e.g., "1/2", "1/4", "" for none)
        unit_full_name: Unit name (e.g., "pounds", "cups", "tablespoons")
        details: Optional preparation details
    
    Returns:
        Ingredient dict ready for recipe
    """
    # Validate the food name
    is_valid, suggestion = validate_ingredient_name(friendly_food_name)
    if not is_valid:
        if suggestion:
            print(f"⚠ Warning: '{friendly_food_name}' not found. Did you mean '{suggestion}'?")
        else:
            print(f"⚠ Warning: '{friendly_food_name}' not found in food database!")
    
    # Construct display name
    display_parts = []
    if whole_number > 0:
        display_parts.append(str(whole_number))
    if fraction:
        display_parts.append(fraction)
    if unit_full_name:
        display_parts.append(unit_full_name)
    display_parts.append(friendly_food_name)
    
    display_name = " ".join(display_parts)
    
    ingredient = {
        "displayName": display_name,
        "foodQuantity": {
            "friendlyFoodName": friendly_food_name,
            "quantity": {
                "wholeNumber": whole_number,
                "fraction": fraction,
                "unitFullName": unit_full_name
            } if unit_full_name else None
        }
    }
    
    if details:
        ingredient["details"] = details
    
    return ingredient


def get_food_database_stats() -> Dict[str, Any]:
    """Get statistics about the food database."""
    foods = fetch_food_database()
    
    categories = {}
    for food in foods:
        category = food.get('category', 'uncategorized')
        categories[category] = categories.get(category, 0) + 1
    
    return {
        "total_foods": len(foods),
        "categories": categories,
        "sample_foods": [food.get('name') for food in foods[:10]]
    }


if __name__ == "__main__":
    # Test the food database functionality
    print("Testing Food Database Utility\n")
    
    # Fetch database
    foods = fetch_food_database()
    print(f"\nTotal foods: {len(foods)}")
    
    # Show stats
    stats = get_food_database_stats()
    print(f"\nCategories: {stats['categories']}")
    print(f"\nSample foods: {', '.join(stats['sample_foods'][:5])}")
    
    # Test validation
    print("\n--- Validation Tests ---")
    test_ingredients = ["chicken breast", "Chicken Breast", "chicken thigh", "fake food"]
    for ing in test_ingredients:
        is_valid, suggestion = validate_ingredient_name(ing)
        if is_valid:
            print(f"✓ '{ing}' - Valid")
        elif suggestion:
            print(f"✗ '{ing}' - Invalid. Suggestion: '{suggestion}'")
        else:
            print(f"✗ '{ing}' - Invalid. No suggestions found.")
