#!/usr/bin/env python3
"""
Refresh all food files to add water content and fix unit issues.

For each food in Foods/, this script:
1. Extracts the FDC ID from the source URL
2. Re-fetches data from FoodData Central API
3. Rebuilds the nutrients list including water
4. Fixes placeholder unit strings (empty strings → canonical units)
5. Preserves human-friendly name, attributes, annotations, and unitOptions

Water is added as the first nutrient after calories since it is a
fundamental property of food composition.
"""

import json
import re
import time
import requests
from datetime import datetime
from pathlib import Path

API_KEY = "eYfxkGm0QcFjJaQI1oINI1ww4nAZDHXGlSkpvPeR"
API_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# FoodData Central nutrient ID → (our name, canonical unit)
# 1008  = Energy (general)
# 2047  = Energy (Atwater General Factors) — used by some Foundation Foods
# 2048  = Energy (Atwater Specific Factors) — also used by Foundation Foods
NUTRIENT_MAPPING = {
    1008: ("calories",          "kcal"),
    2047: ("calories",          "kcal"),   # Atwater General — Foundation Foods
    2048: ("calories",          "kcal"),   # Atwater Specific — Foundation Foods
    1051: ("water",             "g"),
    1003: ("protein",           "g"),
    1004: ("fat",               "g"),
    1005: ("carbohydrates",     "g"),
    1079: ("fiber",             "g"),
    2000: ("sugar",             "g"),
    1087: ("calcium",           "mg"),
    1089: ("iron",              "mg"),
    1090: ("magnesium",         "mg"),
    1091: ("phosphorus",        "mg"),
    1092: ("potassium",         "mg"),
    1093: ("sodium",            "mg"),
    1095: ("zinc",              "mg"),
    1098: ("copper",            "mg"),   # note: was incorrectly "μg" in old script
    1103: ("selenium",          "µg"),
    1099: ("fluoride",          "µg"),
    1162: ("vitaminC",          "mg"),
    1165: ("thiamin",           "mg"),
    1166: ("riboflavin",        "mg"),
    1167: ("niacin",            "mg"),
    1170: ("pantothenicAcid",   "mg"),
    1175: ("vitaminB6",         "mg"),
    1177: ("folate",            "µg"),
    1180: ("choline",           "mg"),
    1178: ("vitaminB12",        "µg"),
    1106: ("vitaminA",          "µg"),
    1109: ("vitaminE",          "mg"),
    1114: ("vitaminD",          "µg"),
    1185: ("vitaminK",          "µg"),
    1258: ("saturatedFat",      "g"),
    1257: ("transFat",          "g"),
    1404: ("alphaLinolenicAcid","g"),
}

# Canonical output order — calories first, water second
NUTRIENT_ORDER = [
    "calories", "water",
    "protein", "fat", "carbohydrates", "fiber", "sugar",
    "calcium", "iron", "magnesium", "phosphorus", "potassium", "sodium",
    "zinc", "copper", "selenium", "fluoride",
    "vitaminC", "thiamin", "riboflavin", "niacin", "pantothenicAcid",
    "vitaminB6", "folate", "choline", "vitaminB12",
    "vitaminA", "vitaminE", "vitaminD", "vitaminK",
    "saturatedFat", "transFat", "alphaLinolenicAcid",
]

# Canonical units for placeholder entries (nutrient not found in USDA data)
CANONICAL_UNITS = {name: unit for _, (name, unit) in NUTRIENT_MAPPING.items()}


def extract_fdc_id(sources: list) -> str | None:
    """Pull the numeric FDC ID out of any USDA URL in the sources list."""
    for source in sources:
        match = re.search(r"api\.nal\.usda\.gov/fdc/v1/food/(\d+)", source)
        if match:
            return match.group(1)
    return None


def fetch_food(fdc_id: str) -> dict | None:
    url = f"{API_BASE_URL}/food/{fdc_id}"
    try:
        response = requests.get(url, params={"api_key": API_KEY}, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    ❌ API error for FDC {fdc_id}: {e}")
        return None


def build_nutrients(food_api_data: dict) -> list:
    """Map API nutrients → our format, in canonical order, with placeholders."""
    # Build a lookup of nutrient name → {name, unit, amount}
    found: dict[str, dict] = {}
    for nutrient_entry in food_api_data.get("foodNutrients", []):
        nutrient = nutrient_entry.get("nutrient", {})
        nid = nutrient.get("id")
        if nid not in NUTRIENT_MAPPING:
            continue
        # Skip kilojoules (keep kcal Energy only)
        if nutrient.get("unitName") == "kJ":
            continue
        our_name, our_unit = NUTRIENT_MAPPING[nid]
        amount = float(nutrient_entry.get("amount") or 0.0)
        found[our_name] = {
            "name": our_name,
            "unit": our_unit,
            "amountPer100g": amount,
        }

    nutrients = []
    for name in NUTRIENT_ORDER:
        if name in found:
            nutrients.append(found[name])
        else:
            # Placeholder — use canonical unit so the field is never empty
            nutrients.append({
                "name": name,
                "unit": CANONICAL_UNITS.get(name, ""),
                "amountPer100g": 0.0,
            })
    return nutrients


def build_unit_options(food_api_data: dict) -> list:
    """Rebuild unit options from the USDA response, always keeping gram first."""
    units = [{
        "unitFullName": "gram",
        "unitAbbreviation": "g",
        "portionInGrams": 1.0,
    }]

    data_type = food_api_data.get("dataType", "")
    for portion in food_api_data.get("foodPortions", []):
        gram_weight = portion.get("gramWeight")
        if not gram_weight:
            continue

        if data_type == "Foundation":
            measure = portion.get("measureUnit", {})
            full_name = measure.get("name", "")
            abbreviation = measure.get("abbreviation", "")
        else:
            # SR Legacy stores the unit description in "modifier"
            full_name = portion.get("modifier", "")
            abbreviation = ""

        if not full_name:
            continue

        units.append({
            "unitFullName": full_name,
            "unitAbbreviation": abbreviation,
            "portionInGrams": float(gram_weight),
        })

    return units


def make_source_string(food_api_data: dict, fdc_id: str) -> str:
    data_type = food_api_data.get("dataType", "FoodData Central")
    label = {
        "Foundation": "Foundation Foods",
        "SR Legacy": "SR Legacy",
    }.get(data_type, data_type)
    description = food_api_data.get("description", f"FDC {fdc_id}")
    today = datetime.today().strftime("%Y-%m-%d")
    return (
        f"U.S. Department of Agriculture, Agricultural Research Service. "
        f"({today}). {description} via {label}. "
        f"USDA FoodData Central. {API_BASE_URL}/food/{fdc_id}"
    )


def refresh_food_file(filepath: Path, dry_run: bool = False) -> str:
    """
    Refresh a single food JSON file.

    Returns a status string: "updated", "skipped", or "error".
    """
    with open(filepath, encoding="utf-8") as f:
        existing = json.load(f)

    human_name = existing.get("name", filepath.stem)
    sources = existing.get("sources", [])
    fdc_id = extract_fdc_id(sources)

    if not fdc_id:
        print(f"  ⚠️  No USDA FDC ID found in sources — skipping")
        return "skipped"

    food_api_data = fetch_food(fdc_id)
    if food_api_data is None:
        return "error"

    nutrients = build_nutrients(food_api_data)
    unit_options = build_unit_options(food_api_data)

    # Preserve manually curated unitOptions when USDA returns none beyond gram
    if len(unit_options) <= 1 and len(existing.get("unitOptions", [])) > 1:
        unit_options = existing["unitOptions"]

    updated = {
        "name": human_name,                    # always preserve
        "nutrients": nutrients,
        "unitOptions": unit_options,
        "attributes": existing.get("attributes", []),   # preserve manual curation
        "annotations": existing.get("annotations", []), # preserve
        "sources": [make_source_string(food_api_data, fdc_id)],
    }

    water_amount = next(
        (n["amountPer100g"] for n in nutrients if n["name"] == "water"), None
    )
    print(f"  ✅ {human_name}: water={water_amount}g/100g  ({len(unit_options)} units)")

    if not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=4, ensure_ascii=False)

    return "updated"


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be changed without writing files")
    parser.add_argument("--food", metavar="FILENAME",
                        help="Process only this file (e.g. Apple.json)")
    args = parser.parse_args()

    foods_dir = Path(__file__).parent.parent / "Foods"
    if not foods_dir.exists():
        print(f"❌ Foods directory not found: {foods_dir}")
        return 1

    if args.food:
        files = [foods_dir / args.food]
    else:
        files = sorted(foods_dir.glob("*.json"))

    total = len(files)
    results = {"updated": 0, "skipped": 0, "error": 0}

    print(f"{'DRY RUN — ' if args.dry_run else ''}Refreshing {total} food files\n")

    for i, filepath in enumerate(files, 1):
        print(f"[{i:3}/{total}] {filepath.name}")
        status = refresh_food_file(filepath, dry_run=args.dry_run)
        results[status] += 1
        # Be polite to the USDA API
        time.sleep(0.25)

    print(f"\n{'='*60}")
    print(f"✅ Updated : {results['updated']}")
    print(f"⚠️  Skipped : {results['skipped']}")
    print(f"❌ Errors  : {results['error']}")
    return 0 if results["error"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
