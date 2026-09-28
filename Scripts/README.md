# Scripts for HumanFriendlyFoods

## Curated meat variants

`Foods/*.json` is the canonical source. Each nutrition-significant raw meat
variant is a **separate, selectable named food** in the existing flat
`{"version": ..., "foods": [...]}` output; do not merge lean/fat trims, grades,
cuts, raw/cooked states, or skin-on/off into one nutrition profile. Keep all
existing `name` values exactly as written: saved recipes refer to those strings.
New names must describe the distinguishing trait, and new FDC IDs must not be
reused for another new food. Existing historical source-ID collisions are not
silently rewritten by this change.

The following entries were verified against the official **FoodData Central SR
Legacy April 2018 CSV** archive. Numbers are per 100 g raw edible portion;
calories are USDA's reported kcal (not a macro-based estimate). Citations with
the complete USDA descriptions and individual FDC URLs are in each food file.

| Food | FDC ID | USDA description | kcal | Protein (g) | Fat (g) | Source portions |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 93% lean ground beef | 173110 | Beef, ground, 93% lean meat / 7% fat, raw | 152 | 20.85 | 7 | 4 oz = 113 g |
| Ribeye cap steak, choice, lean only | 174699 | Beef, ribeye cap steak, boneless, separable lean only, trimmed to 0" fat, choice, raw | 187 | 19.46 | 11.4 | 4 oz = 113 g; 1 steak = 249 g |
| Grass-fed ribeye steak, lean and fat | 173975 | Beef, Australian, imported, grass-fed, rib, ribeye steak/roast lip-on, boneless, separable lean and fat, raw | 217 | 19.8 | 15.21 | 4 oz = 113 g; 1 roast = 350 g |
| Chicken breast, with skin | 171474 | Chicken, broilers or fryers, breast, meat and skin, raw | 172 | 20.85 | 9.25 | 1/2 breast, bone removed = 145 g |

The 4-oz source portion is exposed as a 28.25-g ounce (113/4); the separate
87-g chicken yield from a ready-to-cook whole bird is deliberately excluded
because it is not a serving size for a raw boneless breast. Unreported
micronutrients are omitted rather than represented as measured zero. Source
annotations use `srLegacy`; related pre-existing Foundation entries are not
replaced. In particular, the ribeye-cap choice cut is **not** equivalent to
the existing boneless choice ribeye, and the grass-fed lip-on roast is separately
identified.

To reproduce these four files from USDA (no API key required), run from the
repository root:

```bash
curl -fsSL https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip -o /tmp/sr-legacy.zip
python3 Scripts/import_meat_variants.py /tmp/sr-legacy.zip
python3 Scripts/test_meat_variants.py /tmp/sr-legacy.zip
python3 Scripts/compile_json.py FoodData.json v38
```

The scoped tests check source identity, fat/protein/energy regressions,
uniqueness of names and new source IDs, and byte-deterministic compilation.
The compiler sorts filenames to make the generated artifact reproducible.
`FoodData.json` is ignored and remains a local build artifact; generating it
does not publish or release it. The existing broad validator reports unrelated
historical warnings and is not used as a new all-legacy gate.

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
