#!/usr/bin/env python3
"""Reproduce selected raw meat entries from the official SR Legacy CSV archive."""

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip"
ACCESS_DATE = "2026-09-28"

# FDC ID, exact USDA description, friendly name, filename, attribute template.
VARIANTS = {
    "173110": (
        "Beef, ground, 93% lean meat / 7% fat, raw",
        "93% lean ground beef",
        "NinetyThreePercentGroundBeef.json",
        "EightyPercentGroundBeef.json",
    ),
    "174699": (
        'Beef, ribeye cap steak, boneless, separable lean only, trimmed to 0" fat, choice, raw',
        "Ribeye cap steak, choice, lean only",
        "RibeyeCapSteakChoiceLeanOnly.json",
        "RibeyeSteak.json",
    ),
    "173975": (
        "Beef, Australian, imported, grass-fed, rib, ribeye steak/roast lip-on, boneless, separable lean and fat, raw",
        "Grass-fed ribeye steak, lean and fat",
        "GrassFedRibeyeSteakLeanAndFat.json",
        "RibeyeSteak.json",
    ),
    "171474": (
        "Chicken, broilers or fryers, breast, meat and skin, raw",
        "Chicken breast, with skin",
        "ChickenBreastWithSkin.json",
        "ChickenBreast.json",
    ),
}

# USDA nutrient numbers, not display names (which can change across exports).
NUTRIENTS = {
    "208": "calories", "255": "water", "203": "protein", "204": "fat",
    "205": "carbohydrates", "291": "fiber", "269": "sugar",
    "301": "calcium", "303": "iron", "304": "magnesium",
    "305": "phosphorus", "306": "potassium", "307": "sodium",
    "309": "zinc", "312": "copper", "317": "selenium",
    "313": "fluoride", "401": "vitaminC", "404": "thiamin",
    "405": "riboflavin", "406": "niacin", "410": "pantothenicAcid",
    "415": "vitaminB6", "417": "folate", "421": "choline",
    "418": "vitaminB12", "320": "vitaminA", "323": "vitaminE",
    "328": "vitaminD", "430": "vitaminK", "606": "saturatedFat",
    "605": "transFat", "851": "alphaLinolenicAcid",
}
REQUIRED = {"calories", "protein", "fat", "carbohydrates"}
UNITS = {"G": "g", "MG": "mg", "UG": "µg", "KCAL": "kcal"}


def table(archive, filename):
    matches = [name for name in archive.namelist() if name.endswith("/" + filename + ".csv")]
    if len(matches) != 1:
        raise ValueError(f"Expected one {filename}.csv in USDA archive, found {len(matches)}")
    with archive.open(matches[0]) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def generate(archive_path, foods_dir):
    with zipfile.ZipFile(archive_path) as archive:
        descriptions = {row["fdc_id"]: row for row in table(archive, "food")
                        if row["fdc_id"] in VARIANTS}
        nutrient_numbers = {row["id"]: row for row in table(archive, "nutrient")}
        values = {fdc_id: {} for fdc_id in VARIANTS}
        for row in table(archive, "food_nutrient"):
            fdc_id = row["fdc_id"]
            if fdc_id not in values:
                continue
            source = nutrient_numbers[row["nutrient_id"]]
            number = source["nutrient_nbr"]
            if number not in NUTRIENTS:
                continue
            name = NUTRIENTS[number]
            if name in values[fdc_id]:
                raise ValueError(f"Duplicate {name} nutrient for {fdc_id}")
            if source["unit_name"] not in UNITS:
                raise ValueError(f"Unknown nutrient unit {source['unit_name']} for {fdc_id}")
            values[fdc_id][name] = {
                "name": name, "unit": UNITS[source["unit_name"]],
                "amountPer100g": float(row["amount"]),
            }
        portions = {fdc_id: [] for fdc_id in VARIANTS}
        for row in table(archive, "food_portion"):
            if row["fdc_id"] in portions:
                portions[row["fdc_id"]].append(row)

    generated = {}
    for fdc_id, (description, name, filename, template) in VARIANTS.items():
        record = descriptions.get(fdc_id)
        if record is None or record["description"] != description or record["data_type"] != "sr_legacy_food":
            raise ValueError(f"Unexpected USDA identity/description/type for {fdc_id}: {record}")
        if not REQUIRED <= values[fdc_id].keys():
            raise ValueError(f"Incomplete required nutrients for {fdc_id}")
        units = [{"unitFullName": "gram", "unitAbbreviation": "g", "portionInGrams": 1.0}]
        for portion in portions[fdc_id]:
            label = portion["modifier"].strip()
            weight = float(portion["gram_weight"])
            if label == "oz" and portion["amount"] == "4":
                unit = {"unitFullName": "ounce", "unitAbbreviation": "oz",
                        "portionInGrams": weight / 4}
            elif label == "steak" and portion["amount"] == "1":
                unit = {"unitFullName": "steak", "unitAbbreviation": "",
                        "portionInGrams": weight}
            elif label == "roast" and portion["amount"] == "1":
                unit = {"unitFullName": "roast", "unitAbbreviation": "",
                        "portionInGrams": weight}
            elif label == "breast, bone removed" and portion["amount"] == "0.5":
                unit = {"unitFullName": "half breast", "unitAbbreviation": "",
                        "portionInGrams": weight}
            elif label.startswith("breast, bone removed (yield"):
                continue  # This yield is not a serving weight for a breast.
            else:
                raise ValueError(f"Unreviewed portion {label!r} for {fdc_id}")
            units.append(unit)
        if len(units) == 1:
            raise ValueError(f"No USDA serving portions for {fdc_id}")
        attributes = json.loads((foods_dir / template).read_text(encoding="utf-8"))["attributes"]
        generated[filename] = {
            "name": name,
            "nutrients": [values[fdc_id][key] for key in NUTRIENTS.values()
                          if key in values[fdc_id]],
            "unitOptions": units,
            "attributes": attributes,
            "annotations": ["srLegacy"],
            "sources": [
                f"U.S. Department of Agriculture, Agricultural Research Service. "
                f"({ACCESS_DATE}). {description} via SR Legacy. USDA FoodData Central. "
                f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
            ],
        }
    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help=f"Official SR Legacy CSV ZIP: {ARCHIVE_URL}")
    args = parser.parse_args()
    for filename, food in generate(args.archive, ROOT / "Foods").items():
        (ROOT / "Foods" / filename).write_text(
            json.dumps(food, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
        )
        print(f"Foods/{filename}: {food['name']}")
