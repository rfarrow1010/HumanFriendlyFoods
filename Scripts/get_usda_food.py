import json
import requests
import argparse
import os
from datetime import datetime

def fetch(api_key: str, fdcId: str) -> dict:
    URL = f"https://api.nal.usda.gov/fdc/v1/food/{fdcId}?api_key={api_key}"
    response = requests.get(URL)
    if response.status_code != 200:
        print(f"Received status code {response.status_code}. Exiting")
        exit(1)

    return response.json()

def space_name(name: str) -> str:
    spaced_name = name[0]

    for letter in name[1:]:
        if letter.isupper():
            spaced_name += " "

        spaced_name += letter.lower()

    return spaced_name

def parse(json_dict: dict, fdcId: str, name: str) -> dict:
    NUTRIENT_NAME_MAP = {
        "Energy": "calories",
        "Protein": "protein",
        "Total lipid (fat)": "fat",
        # TODO: make some logic to choose whichever of these two exists
        #"Carbohydrates": "carbohydrates",
        "Carbohydrate, by difference": "carbohydrates",
        "Fiber, total dietary": "fiber",
        "Total Sugars": "sugar",
        "Calcium, Ca": "calcium",
        "Iron, Fe": "iron",
        "Magnesium, Mg": "magnesium",
        "Phosphorus, P": "phosphorus",
        "Potassium, K": "potassium",
        "Sodium, Na": "sodium",
        "Zinc, Zn": "zinc",
        "Copper, Cu": "copper",
        "Selenium, Se": "selenium",
        "Fluoride, F": "fluoride",
        "Vitamin C, total ascorbic acid": "vitaminC",
        "Thiamin": "thiamin",
        "Riboflavin": "riboflavin",
        "Niacin": "niacin",
        "Pantothenic acid": "pantothenicAcid",
        "Vitamin B-6": "vitaminB6",
        "Folate, total": "folate",
        "Choline, total": "choline",
        "Vitamin B-12": "vitaminB12",
        "Vitamin A, RAE": "vitaminA",
        "Vitamin E (alpha-tocopherol)": "vitaminE",
        "Vitamin D (D2 + D3)": "vitaminD",
        "Vitamin K (phylloquinone)": "vitaminK",
        "Fatty acids, total saturated": "saturatedFat",
        "Fatty acids, total trans": "transFat",
        "": "biotin",
        "": "chloride",
        "": "chromium",
        "": "iodine",
        "": "molybdenum",
        "": "linoleicAcid",
        "": "alphaLinolenicAcid"
    }

    spaced_name = space_name(name)
    nutrients_written = []

    # initialize everything with 1 gram as a unit option to base other units off of
    food = {
        "name": spaced_name,
        "nutrients": [],
        "unitOptions": [{
            "unitFullName": "gram",
            "unitAbbreviation": "g",
            "portionInGrams": 1.0
        }]
    }

    source_nutrients = json_dict["foodNutrients"]
    source_units = json_dict.get("foodPortions", [])

    for nutrient in source_nutrients:
        source_nutrient_name = nutrient["nutrient"]["name"]
        if source_nutrient_name not in NUTRIENT_NAME_MAP.keys():
            continue
    
        nutrient_unit = nutrient["nutrient"]["unitName"]
        amount = nutrient["amount"]

        nutrient_name = NUTRIENT_NAME_MAP[source_nutrient_name]
        if nutrient_name is None:
            continue

        # skip kilojoules
        if nutrient_unit == "kJ":
            continue

        food["nutrients"].append(
            {
                "name": nutrient_name,
                "unit": nutrient_unit,
                "amountPer100g": amount
            }
        )

        nutrients_written.append(nutrient_name)

    for unit in source_units:
        # NOTE: the path to which units are written appears to be a point of divergence between
        # Foundation Foods and SR Legacy
        unitFullName: str = ""
        unitAbbreviation: str = ""
        if json_dict["dataType"] == "Foundation":
            unitFullName = unit["measureUnit"]["name"]
            unitAbbreviation = unit["measureUnit"]["abbreviation"]
        else:
            unitFullName = unit["modifier"]

        portionInGrams = unit["gramWeight"]

        food["unitOptions"].append(
            {
                "unitFullName": unitFullName,
                "unitAbbreviation": unitAbbreviation,
                "portionInGrams": portionInGrams
            }
        )

    resource_title_data_source: str = "unspecified"
    if json_dict["dataType"] == "Foundation":
        resource_title_data_source = "Foundation Foods"
    elif json_dict["dataType"] == "SR Legacy":
        resource_title_data_source = "SR Legacy"

    SOURCE_STR = f"U.S. Department of Agriculture, Agricultural Research Service. ({datetime.today().strftime('%Y-%m-%d')}). {spaced_name} via {resource_title_data_source}. USDA FoodData Central. https://api.nal.usda.gov/fdc/v1/food/{fdcId}"

    food["attributes"] = []
    # for notes about the app that should not be exposed to the user for goal tracking
    food["annotations"] = []
    if json_dict["dataType"] == "Foundation":
        food["annotations"].append("foundation")
    elif json_dict["dataType"] == "SR Legacy":
        food["annotations"].append("srLegacy")
    food["sources"] = [
        SOURCE_STR
    ]

    # make placeholders for any missing nutrients
    for nutrient in NUTRIENT_NAME_MAP.values():
        if nutrient not in nutrients_written:
            food["nutrients"].append({
                "name": nutrient,
                "unit": "",
                "amountPer100g": 0.0
            })

    return food

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='''
        This script creates a Human Friendly Food from an SR Legacy entry. 
        It uses a user-supplied API key to fetch the entry from the FoodData Central API 
        and parses the entry into the Human Friendly Food format.
        An FDC ID must be supplied, which can be found on an SR Legacy entry's webpage.
        A human friendly name must also be supplied.
        This script does not produce a finished product. The user must add unit option
        abbreviations as well as relevant attributes.
        '''
    )
    parser.add_argument("api_key", help="Your API key for FoodData Central.")
    parser.add_argument("fdcId", help="The FDC ID of the given SR Legacy food. This is a numerical value.")
    parser.add_argument("name", help="The human friendly name for this food.")

    args = parser.parse_args()
    api_key = args.api_key
    fdcId = args.fdcId
    name = args.name

    if not all(x.isalpha() or x.isspace() for x in name):
        print("Non-alphabet or whitespace letters in the supplied name. Exiting.")
        exit(1)

    with os.scandir("../Foods") as entries:
        for entry in entries:
            if entry.name == f"{name}.json":
                print(f"Entry with name {name} already exists")
                exit(1)

    fetched_json_dict = fetch(api_key=api_key, fdcId=fdcId)
    food_dict = parse(json_dict=fetched_json_dict, fdcId=fdcId, name=name)

    underscored_name = name.replace(" ", "_")
    with open(f"../Foods/{underscored_name}.json", "w") as out_file:
        json.dump(food_dict, out_file, ensure_ascii=False, indent=4)

    print(f"File written to `Foods/{name}.json`. Please add missing information and double-check for accuracy.")