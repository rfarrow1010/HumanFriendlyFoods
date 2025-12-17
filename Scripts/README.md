# Scripts for HumanFriendlyFoods

## add_missing_ingredients.py

This script fetches nutritional data from the USDA FoodData Central API and creates individual JSON files in the `Foods/` directory.

### Prerequisites

1. Install required Python package:
   ```bash
   pip install requests
   ```

2. (Optional) Get a FoodData Central API key:
   - Visit https://fdc.nal.usda.gov/api-key-signup.html
   - Sign up for a free API key
   - Replace `DEMO_KEY` in the script with your key (the demo key works but has rate limits)

### Usage

1. Edit the `MISSING_INGREDIENTS` list in the script to add the ingredients you want
2. Run the script:
   ```bash
   python3 Scripts/add_missing_ingredients.py
   ```

### How it works

1. **Searches FoodData Central**: For each ingredient, the script searches the USDA database
2. **Fetches detailed nutrition data**: Gets comprehensive nutrient information
3. **Converts to project format**: Transforms the data into the standard format used by this project
4. **Determines attributes**: Automatically assigns dietary attributes (vegetarian, vegan, gluten-free, etc.)
5. **Creates JSON file**: Saves the food as `Foods/[FoodName].json` in PascalCase format

### Output

The script creates JSON files with the following structure:
- `name`: The food name from FoodData Central
- `nutrients`: Array of 32+ nutrients with amounts per 100g
- `unitOptions`: Default gram measurements
- `attributes`: Dietary flags (vegetarian, vegan, halal, kosher, etc.)
- `annotations`: Data source type (foundation, sr_legacy)
- `sources`: Citation for the USDA data

### Notes

- Files are named in PascalCase (e.g., "sesame oil" → `SesameOil.json`)
- If a file already exists, it will be skipped
- Some specialty ingredients may not be in FoodData Central
- The script automatically determines dietary attributes based on ingredient name and type
