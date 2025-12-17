#!/usr/bin/env python3
"""
Add missing ingredients to the Foods directory.
This script fetches nutritional data from FoodData Central API for ingredients
and creates individual JSON files in the Foods directory.
"""

import json
import os
import sys
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# FoodData Central API configuration
API_KEY = "eYfxkGm0QcFjJaQI1oINI1ww4nAZDHXGlSkpvPeR"
API_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# List of missing ingredients to add
# Format: (search_query, suggested_name, suggested_filename)
MISSING_INGREDIENTS = [
    # Korean
    ("sesame oil", "Sesame oil", "SesameOil"),
    ("gochugaru korean red pepper flakes", "Gochugaru", "Gochugaru"),
    ("gochujang korean chili paste", "Gochujang", "Gochujang"),
    ("rice vinegar", "Rice vinegar", "RiceVinegar"),
    ("green onions", "Green onions", "GreenOnions"),
    ("pork belly raw", "Raw pork belly", "RawPorkBelly"),
    ("napa cabbage raw", "Raw napa cabbage", "RawNapaCabbage"),
    ("bean sprouts raw", "Raw bean sprouts", "RawBeanSprouts"),
    ("shiitake mushrooms raw", "Raw shiitake mushrooms", "RawShiitakeMushrooms"),
    
    # Mexican
    ("cilantro raw", "Raw cilantro", "RawCilantro"),
    ("jalapeño peppers raw", "Raw jalapeño peppers", "RawJalapenoPeppers"),
    
    # Mediterranean/Middle Eastern
    ("kalamata olives", "Kalamata olives", "KalamataOlives"),
    ("eggplant raw", "Raw eggplant", "RawEggplant"),
    ("mint raw", "Raw mint", "RawMint"),
    
    # Thai
    ("snap peas raw", "Raw snap peas", "RawSnapPeas"),
    ("red curry paste", "Red curry paste", "RedCurryPaste"),
    ("lemongrass raw", "Raw lemongrass", "RawLemongrass"),
    ("bamboo shoots", "Bamboo shoots", "BambooShoots"),
    
    # Indian
    ("curry powder", "Curry powder", "CurryPowder"),
    ("garam masala", "Garam masala", "GaramMasala"),
    ("basmati rice raw", "Raw basmati rice", "RawBasmatiRice"),
    
    # Japanese
    ("mirin", "Mirin", "Mirin"),
    ("dashi", "Dashi", "Dashi"),
    ("seaweed nori", "Nori seaweed", "NoriSeaweed"),
    ("short grain rice raw", "Raw short-grain rice", "RawShortGrainRice"),
    
    # Chinese
    ("oyster sauce", "Oyster sauce", "OysterSauce"),
    ("jasmine rice raw", "Raw jasmine rice", "RawJasmineRice"),
    
    # Middle Eastern/Persian
    ("ground lamb raw", "Raw ground lamb", "RawGroundLamb"),
    ("sumac spice", "Sumac", "Sumac"),
    ("saffron", "Saffron", "Saffron"),
    ("dried lime", "Dried lime", "DriedLime"),
    ("pomegranate molasses", "Pomegranate molasses", "PomegranateMolasses"),
    ("barberries dried", "Dried barberries", "DriedBarberries"),
    ("dill fresh", "Fresh dill", "FreshDill"),
    ("lamb raw", "Raw lamb", "RawLamb"),
    
    # Eastern European
    ("caraway seeds", "Caraway seeds", "CarawaySeeds"),
    ("beets raw", "Raw beets", "RawBeets"),
    ("black pepper", "Black pepper", "BlackPepper"),
]

# Nutrient mapping from FoodData Central to our format
NUTRIENT_MAPPING = {
    1008: ("calories", "kcal"),
    1003: ("protein", "g"),
    1004: ("fat", "g"),
    1005: ("carbohydrates", "g"),
    1079: ("fiber", "g"),
    2000: ("sugar", "g"),
    1087: ("calcium", "mg"),
    1089: ("iron", "mg"),
    1090: ("magnesium", "mg"),
    1091: ("phosphorus", "mg"),
    1092: ("potassium", "mg"),
    1093: ("sodium", "mg"),
    1095: ("zinc", "mg"),
    1098: ("copper", "μg"),
    1103: ("selenium", "μg"),
    1099: ("fluoride", "mg"),
    1162: ("vitaminC", "mg"),
    1165: ("thiamin", "mg"),
    1166: ("riboflavin", "mg"),
    1167: ("niacin", "mg"),
    1170: ("pantothenicAcid", "mg"),
    1175: ("vitaminB6", "mg"),
    1177: ("folate", "μg"),
    1180: ("choline", "mg"),
    1178: ("vitaminB12", "μg"),
    1106: ("vitaminA", "μg"),
    1109: ("vitaminE", "mg"),
    1114: ("vitaminD", "μg"),
    1185: ("vitaminK", "μg"),
    1258: ("saturatedFat", "g"),
    1257: ("transFat", "g"),
    1404: ("alphaLinolenicAcid", "g"),
}


def to_pascal_case(name: str) -> str:
    """Convert a name to PascalCase for filename - but we'll use suggested names instead."""
    return name


def search_food(query: str) -> Optional[Dict]:
    """Search for food in FoodData Central API."""
    url = f"{API_BASE_URL}/foods/search"
    params = {
        "query": query,
        "api_key": API_KEY,
        "dataType": ["Foundation", "SR Legacy"],
        "pageSize": 5
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("foods"):
            # Return the first result
            return data["foods"][0]
        return None
    except Exception as e:
        print(f"    Error searching for {query}: {e}")
        return None


def get_food_details(fdc_id: int) -> Optional[Dict]:
    """Get detailed food information from FoodData Central API."""
    url = f"{API_BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    Error fetching details for FDC ID {fdc_id}: {e}")
        return None


def determine_attributes(food_name: str, food_data: Dict) -> List[str]:
    """Determine dietary attributes based on food name and data."""
    name_lower = food_name.lower()
    attributes = []
    
    # Check for animal products
    animal_keywords = ["meat", "beef", "pork", "chicken", "lamb", "fish", "salmon", "tuna"]
    is_animal = any(kw in name_lower for kw in animal_keywords)
    
    dairy_keywords = ["milk", "cheese", "cream", "butter", "yogurt"]
    is_dairy = any(kw in name_lower for kw in dairy_keywords)
    
    nut_keywords = ["almond", "peanut", "cashew", "walnut", "pecan", "hazelnut"]
    has_nuts = any(kw in name_lower for kw in nut_keywords)
    
    soy_keywords = ["soy", "tofu", "tempeh", "edamame"]
    has_soy = any(kw in name_lower for kw in soy_keywords)
    
    egg_keywords = ["egg"]
    has_egg = any(kw in name_lower for kw in egg_keywords)
    
    # Determine attributes
    if not is_animal and not is_dairy and not has_egg:
        attributes.append("vegetarian")
    
    if not is_animal and not is_dairy and not has_egg:
        attributes.append("vegan")
    
    if is_animal and "pork" not in name_lower:
        attributes.append("animalMeat")
    
    # Most whole foods are gluten-free unless they're grains
    grain_keywords = ["wheat", "barley", "rye", "bread", "pasta", "flour"]
    if not any(kw in name_lower for kw in grain_keywords):
        attributes.append("glutenFree")
    
    if not is_dairy:
        attributes.append("lactoseIntolerant")
    
    if not has_nuts:
        attributes.append("nutFree")
    
    if not has_soy:
        attributes.append("soyFree")
    
    if not has_egg:
        attributes.append("eggFree")
    
    # Halal - exclude pork
    if "pork" not in name_lower:
        attributes.append("halal")
    
    # Kosher - exclude pork and shellfish
    shellfish_keywords = ["shrimp", "lobster", "crab", "oyster", "clam", "mussel"]
    if "pork" not in name_lower and not any(kw in name_lower for kw in shellfish_keywords):
        attributes.append("kosher")
    
    return attributes


def create_food_json(food_data: Dict, display_name: str) -> Dict:
    """Convert FoodData Central data to our JSON format."""
    food_json = {
        "name": display_name,  # Use our custom display name
        "nutrients": [],
        "unitOptions": [
            {
                "unitFullName": "gram",
                "unitAbbreviation": "g",
                "portionInGrams": 1.0
            }
        ],
        "attributes": [],
        "annotations": [],
        "sources": []
    }
    
    # Extract nutrients
    nutrients_dict = {}
    for nutrient in food_data.get("foodNutrients", []):
        nutrient_id = nutrient.get("nutrient", {}).get("id") or nutrient.get("nutrientId")
        if nutrient_id in NUTRIENT_MAPPING:
            name, unit = NUTRIENT_MAPPING[nutrient_id]
            amount = nutrient.get("amount", 0.0) or 0.0
            nutrients_dict[name] = {
                "name": name,
                "unit": unit,
                "amountPer100g": float(amount)
            }
    
    # Add all nutrients in consistent order
    nutrient_order = ["calories", "protein", "fat", "carbohydrates", "fiber", "sugar",
                     "calcium", "iron", "magnesium", "phosphorus", "potassium", "sodium",
                     "zinc", "copper", "selenium", "fluoride", "vitaminC", "thiamin",
                     "riboflavin", "niacin", "pantothenicAcid", "vitaminB6", "folate",
                     "choline", "vitaminB12", "vitaminA", "vitaminE", "vitaminD",
                     "vitaminK", "saturatedFat", "transFat", "alphaLinolenicAcid"]
    
    for nutrient_name in nutrient_order:
        if nutrient_name in nutrients_dict:
            food_json["nutrients"].append(nutrients_dict[nutrient_name])
        else:
            # Add placeholder with empty unit
            unit = ""
            if nutrient_name in ["calories"]:
                unit = "kcal"
            food_json["nutrients"].append({
                "name": nutrient_name,
                "unit": unit,
                "amountPer100g": 0.0
            })
    
    # Determine attributes
    food_json["attributes"] = determine_attributes(food_json["name"], food_data)
    
    # Add annotations
    data_type = food_data.get("dataType", "").lower()
    if "foundation" in data_type:
        food_json["annotations"].append("foundation")
    elif "sr legacy" in data_type:
        food_json["annotations"].append("sr_legacy")
    
    # Add source
    fdc_id = food_data.get("fdcId")
    if fdc_id:
        description = food_data.get("description", display_name)
        food_json["sources"].append(
            f"U.S. Department of Agriculture, Agricultural Research Service. (2025-02-05). "
            f"{description} via {food_data.get('dataType', 'FoodData Central')}. "
            f"USDA FoodData Central. https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
        )
    
    return food_json


def save_food_file(food_json: Dict, filename: str, foods_dir: Path) -> bool:
    """Save food JSON to a file in the Foods directory."""
    try:
        filepath = foods_dir / f"{filename}.json"
        
        # Check if file already exists
        if filepath.exists():
            print(f"    ⚠️  File already exists: {filename}.json")
            return False
        
        # Write JSON file with proper formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(food_json, f, indent=4, ensure_ascii=False)
        
        print(f"    ✅ Created: {filename}.json")
        return True
    except Exception as e:
        print(f"    ❌ Error saving file: {e}")
        return False


def main():
    print("=" * 70)
    print("Adding Missing Ingredients to Foods Directory")
    print("=" * 70)
    print(f"\nTotal ingredients to add: {len(MISSING_INGREDIENTS)}\n")
    
    # Get the Foods directory path
    script_dir = Path(__file__).parent
    foods_dir = script_dir.parent / "Foods"
    
    if not foods_dir.exists():
        print(f"❌ Foods directory not found: {foods_dir}")
        return 1
    
    print(f"📁 Foods directory: {foods_dir}\n")
    
    # Track results
    added = []
    skipped = []
    failed = []
    cancelled = []
    
    # Add each ingredient
    for i, (search_query, display_name, filename) in enumerate(MISSING_INGREDIENTS, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(MISSING_INGREDIENTS)}] Processing: {search_query}")
        print(f"{'='*70}")
        
        try:
            # Search for the food
            print(f"🔍 Searching USDA database for: {search_query}")
            search_result = search_food(search_query)
            if not search_result:
                failed.append(search_query)
                print(f"    ❌ Not found in FoodData Central")
                continue
            
            # Get detailed information
            fdc_id = search_result.get("fdcId")
            if not fdc_id:
                failed.append(search_query)
                print(f"    ❌ No FDC ID found")
                continue
            
            print(f"✅ Found: {search_result.get('description')}")
            print(f"   FDC ID: {fdc_id}")
            print(f"   Data Type: {search_result.get('dataType')}")
            
            food_data = get_food_details(fdc_id)
            
            if not food_data:
                failed.append(search_query)
                print(f"    ❌ Could not fetch details")
                continue
            
            # Create JSON structure
            food_json = create_food_json(food_data, display_name)
            
            # Show preview
            print(f"\n📋 Preview:")
            print(f"   Display Name: {display_name}")
            print(f"   Filename: {filename}.json")
            print(f"   Attributes: {', '.join(food_json['attributes'])}")
            print(f"   Calories (per 100g): {next((n['amountPer100g'] for n in food_json['nutrients'] if n['name'] == 'calories'), 'N/A')}")
            print(f"   Protein (per 100g): {next((n['amountPer100g'] for n in food_json['nutrients'] if n['name'] == 'protein'), 'N/A')}g")
            
            # Ask for approval
            print(f"\n❓ Create this food file?")
            print(f"   [y] Yes, create {filename}.json")
            print(f"   [n] No, skip this ingredient")
            print(f"   [e] Edit the display name or filename")
            print(f"   [q] Quit")
            
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'q':
                print("\n🛑 Stopped by user")
                cancelled.extend([item[0] for item in MISSING_INGREDIENTS[i:]])
                break
            elif choice == 'n':
                skipped.append(search_query)
                print(f"⏭️  Skipped")
                continue
            elif choice == 'e':
                # Allow editing
                new_display = input(f"Enter display name [{display_name}]: ").strip()
                if new_display:
                    display_name = new_display
                    food_json["name"] = display_name
                
                new_filename = input(f"Enter filename (without .json) [{filename}]: ").strip()
                if new_filename:
                    filename = new_filename
                
                print(f"✏️  Updated to: {display_name} → {filename}.json")
            elif choice != 'y':
                print(f"Invalid choice, skipping...")
                skipped.append(search_query)
                continue
            
            # Save the file
            if save_food_file(food_json, filename, foods_dir):
                added.append(search_query)
            else:
                skipped.append(search_query)
                
        except Exception as e:
            failed.append(search_query)
            print(f"    ❌ Error: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n✅ Successfully added: {len(added)}/{len(MISSING_INGREDIENTS)}")
    print(f"⏭️  Skipped: {len(skipped)}/{len(MISSING_INGREDIENTS)}")
    print(f"❌ Failed: {len(failed)}/{len(MISSING_INGREDIENTS)}")
    if cancelled:
        print(f"🛑 Cancelled: {len(cancelled)}/{len(MISSING_INGREDIENTS)}")
    
    if added:
        print("\n✅ Added ingredients:")
        for ingredient in added:
            print(f"  - {ingredient}")
    
    if skipped:
        print("\n⏭️  Skipped ingredients:")
        for ingredient in skipped:
            print(f"  - {ingredient}")
    
    if failed:
        print("\n❌ Failed ingredients:")
        for ingredient in failed:
            print(f"  - {ingredient}")
        print("\nNote: Some specialty items may not be in FoodData Central.")
        print("You may need to add these manually or use closest equivalents.")
    
    print(f"\n� Food files saved to: {foods_dir}")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
