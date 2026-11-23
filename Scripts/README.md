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

## Sourced salmon mass units and rice vinegar (v39 candidate)

This change builds on the 234-food meat-variant source tree and preserves every
existing name and nutrition profile. It adds **Rice vinegar**, making 235 foods.
Compile only through `Scripts/compile_json.py`; the ignored `FoodData-v39.json`
is a local candidate, not a published release:

```bash
python3 Scripts/test_salmon_vinegar.py
python3 Scripts/test_meat_variants.py /path/to/sr-legacy.zip
python3 Scripts/compile_json.py FoodData-v39.json v39
```

**Salmon:** the exact primary Foundation record is
[FDC 2684441](https://api.nal.usda.gov/fdc/v1/food/2684441),
`Fish, salmon, Atlantic, farm raised, raw`. The October 2026 Foundation archive
confirms its only portion is 1 RACC = 115 g. Repository policy excludes RACC;
it is not relabeled as a fillet or serving. Nutrients are unchanged, including
pre-existing legacy placeholders; this is not a full nutrient re-audit.

**Rice vinegar:** Japan's government MEXT
[food 17016, table 01, Supplement 2023](https://fooddb.mext.go.jp/details/details.pl?ITEM_NO=17_17016_7&MODE=0&WEIGHT=100)
has exact English description `SEASONINGS AND SPICES/Vinegar/rice vinegar`.
Its Japanese rice-vinegar profile reports 46 kcal, 0.2 g protein, 0 g fat,
7.4 g carbohydrates and 12 mg sodium per 100 g edible portion. Reported kcal
includes energy not represented by the three macros (organic acids are present).
Only explicitly numeric values are imported; `Tr`, `-`, and parenthesized
estimated values are omitted. Sugar is not inferred from carbohydrates. The
record uses `mext` provenance, not a fabricated USDA ID, and is not rice wine,
seasoned sushi vinegar, or a claim that all rice-vinegar brands are identical.
Vegetarian/vegan are the only dietary attributes; allergy/certification claims
are not inferred from the food name.

**Portions:** both records expose gram = 1 g, avoirdupois ounce =
28.349523125 g, and pound = 453.59237 g, exactly, from
[NIST Handbook 133 (2026), Appendix E](https://www.nist.gov/system/files/documents/2025/12/23/2026_NIST_HB133_AppendixE-20251222.docx).
These are mass definitions, not fluid-volume conversions or estimated servings.
No rice-vinegar tsp/tbsp/cup weight was verified for this profile; those units
remain absent rather than borrowing distilled-vinegar density.

**Deliberately open gaps (checked 2026-11-23):** complete current USDA
[downloads](https://fdc.nal.usda.gov/download-datasets/) contain no vinegar in
Foundation (October 2026), only the four already-present vinegar types in SR
Legacy (April 2018), and only generic `Vinegar` (FDC 2709351) in FNDDS
(2021-2023). No distinct government-backed white-wine profile was verified.
[UK CoFID 2021](https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid)
food 17-339 combines malt, cider and wine samples;
[Australian AFCD Release 3](https://www.foodstandards.gov.au/science-data/food-nutrient-databases/afcd/data-files)
food F009498 combines white, brown and malt vinegar. Neither is a matching
white-wine source. MEXT 17017 is wine vinegar without a white/red distinction.
USDA branded white-wine records largely specify mL-only servings and rounded
labels, not a generic profile or a verified gram conversion. The gram-based
Napa Valley record FDC 1866254 includes grape must, unlike the manufacturer's
current ingredient listing; it was not imported. White-wine and other
unsubstantiated variants stay open, as requested, rather than repurposing
existing distilled/red-wine records.

**Supplementary-portion review:** USDA SR Legacy independently confirms the
existing Golden Delicious apple FDC 168202 portions (small 129 g, medium 169 g,
large 215 g, sliced cup 109 g) and raw long-grain rice FDC 169756/169703 cup
185 g. The old downstream generic-apple 149/182 g and generic-rice 210 g claims
are not replacements for these cultivar/state-matching sources. No additional
rice/apple source changes are needed.

The focused test is wired into food-validation CI before the historical broad
validator. It checks flat schema, unique identities, exact positive mass weights
and metrology citations, MEXT nutrient/unknown-value regressions, and
byte-deterministic source-preserving compilation. Historical broad-validator
warnings are not silently fixed by this scoped change: both the 234-food baseline
and this candidate have 7 required-macro warnings and 9 high-zero warnings.
The broad validator's indiscriminate zero-macro list grows from 49 to 50 because
MEXT explicitly reports rice vinegar's fat as zero; the scoped source gate
accepts that reported zero, not an unknown-value placeholder.

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
