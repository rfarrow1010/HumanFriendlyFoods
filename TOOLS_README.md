# Food Database Validation and Classification Tools

This repository includes automated tools for validating data quality and classifying foods according to USDA MyPlate food groups.

## Data Validation

### validate_food_data.py

Identifies data quality issues in the food database:

#### Issues Detected:
- **Missing Units**: Nutrients with values but empty unit strings
- **High Zero Percentage**: Foods where >70% of nutrients are 0.0
- **Zero Macronutrients**: Implausible 0.0 values for calories, protein, fat, or carbs

#### Usage:

```bash
# Basic validation scan
python3 Scripts/validate_food_data.py

# Export issues to JSON for programmatic processing
python3 Scripts/validate_food_data.py --export issues.json

# Verbose mode (includes unit option suggestions)
python3 Scripts/validate_food_data.py --verbose
```

### GitHub Actions Integration

The validation script runs automatically on pull requests that modify files in the `Foods/` directory. The workflow:

1. Runs validation on all food files
2. Fails the check if any critical issues are found
3. Posts a detailed comment on the PR with the issues
4. Uploads a JSON artifact with issue details

**Location**: `.github/workflows/validate-foods.yml`

To enable this as a required check:
1. Go to your repository Settings → Branches
2. Add a branch protection rule for `main`
3. Enable "Require status checks to pass before merging"
4. Select "validate / Validate Food Database"

## MyPlate Food Group Classification

### myplate_classifier.py

Automatically classifies foods into USDA MyPlate food groups and subgroups using pattern matching.

#### Food Groups (from [MyPlate.gov](https://www.myplate.gov/eat-healthy/food-group-gallery)):
- **fruit**: Any fruit or 100% fruit juice
- **vegetable**: Any vegetable or 100% vegetable juice  
- **grain**: Foods made from wheat, rice, oats, cornmeal, barley, or other cereal grains
- **protein**: Meat, poultry, seafood, beans, peas, lentils, eggs, nuts, seeds, soy products
- **dairy**: Milk, yogurt, cheese, and fortified soy beverages

#### Subgroups (from [Dietary Guidelines](https://www.dietaryguidelines.gov/sites/default/files/2020-12/Dietary_Guidelines_for_Americans_2020-2025.pdf)):

**Fruits:**
- `wholeFruit`: Fresh, frozen, canned whole fruits
- `fruitJuice`: 100% fruit juice

**Vegetables:**
- `darkGreenVegetable`: Bok choy, broccoli, collards, kale, spinach, etc.
- `redOrangeVegetable`: Carrots, pumpkin, red peppers, sweet potato, tomatoes, etc.
- `beansPeasLentils`: Black beans, chickpeas, kidney beans, lentils, pinto beans, split peas
- `starchyVegetable`: Cassava, corn, green peas, plantains, potatoes, taro, etc.
- `otherVegetable`: Artichokes, asparagus, beets, cabbage, cauliflower, celery, cucumbers, etc.

**Grains:**
- `wholeGrain`: Brown rice, oatmeal, whole wheat bread, quinoa, etc.
- `refinedGrain`: White bread, white rice, pasta, flour tortilla, etc.

**Protein Foods:**
- `meatPoultryEggs`: Beef, chicken, turkey, pork, eggs, etc.
- `seafood`: Fish (salmon, tuna, cod) and shellfish (shrimp, crab)
- `nutsSeedsSoy`: Almonds, cashews, chia seeds, tofu, tempeh, etc.
- `beansPeasLentils`: Same as vegetable subgroup (dual classification)

**Dairy:**
- `milk`: Milk, lactose-free milk, fortified soy milk
- `yogurt`: Yogurt, Greek yogurt
- `cheese`: Hard cheese, soft cheese, cottage cheese

#### Special Handling: Dual Classification

**Beans, peas, and lentils** are classified as **BOTH** `vegetable` AND `protein` per MyPlate guidelines, since they can count toward either food group depending on dietary needs.

#### Usage:

```bash
# Analyze without making changes
python3 Scripts/myplate_classifier.py --analyze-only

# Dry run - see what would be modified
python3 Scripts/myplate_classifier.py

# Apply classifications to files
python3 Scripts/myplate_classifier.py --apply
```

#### What It Does:

1. **Adds food group attributes** to each food's `attributes` array
2. **Adds subgroup attributes** based on specific food characteristics
3. **Adds cup units** to fruits and vegetables (with `portionInGrams: 0.0` placeholder)

#### Manual Steps Required:

After running with `--apply`, you need to:
1. Review the classifications for accuracy
2. **Update `portionInGrams` values** for newly added cup units (the script adds 0.0 as a placeholder)
3. Handle uncategorized foods manually (condiments, oils, spices, etc.)

## Examples

### Validating a specific food file:

```bash
# Check if CanolaOil.json has issues
python3 Scripts/validate_food_data.py | grep -A5 "CanolaOil"
```

### Classifying a specific category:

```bash
# See all protein foods
python3 Scripts/myplate_classifier.py --analyze-only | grep -A20 "PROTEIN"
```

### Identifying foods that need cup measurements:

```bash
# List foods missing cup units
python3 Scripts/myplate_classifier.py --analyze-only | grep -A100 "NEEDS CUP UNITS"
```

## Development

Both scripts are designed to be:
- **Non-destructive by default** (dry-run mode)
- **Extensible** (easy to add new patterns or rules)
- **Informative** (detailed reporting of what was found/changed)

To add new food patterns, edit the `CLASSIFICATION_RULES` dictionary in `myplate_classifier.py`.

To adjust validation thresholds, modify the constants in `validate_food_data.py` (e.g., the 70% zero threshold).
