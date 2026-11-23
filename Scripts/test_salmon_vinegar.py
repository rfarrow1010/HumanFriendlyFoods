"""Scoped source, schema and portion regressions for salmon and rice vinegar."""

import json
import math
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NIST_URL = (
    "https://www.nist.gov/system/files/documents/2025/12/23/"
    "2026_NIST_HB133_AppendixE-20251222.docx"
)
MEXT_URL = (
    "https://fooddb.mext.go.jp/details/details.pl?"
    "ITEM_NO=17_17016_7&MODE=0&WEIGHT=100"
)
RICE_VALUES = {
    "calories": ("kcal", 46), "water": ("g", 87.9),
    "protein": ("g", 0.2), "fat": ("g", 0), "carbohydrates": ("g", 7.4),
    "calcium": ("mg", 2), "iron": ("mg", 0.1), "magnesium": ("mg", 6),
    "phosphorus": ("mg", 15), "potassium": ("mg", 16),
    "sodium": ("mg", 12), "zinc": ("mg", 0.2),
    "iodine": ("\u00b5g", 0), "chromium": ("\u00b5g", 1),
    "molybdenum": ("\u00b5g", 4), "vitaminA": ("\u00b5g", 0),
    "thiamin": ("mg", 0.01), "riboflavin": ("mg", 0.01),
    "niacin": ("mg", 0.3), "vitaminB6": ("mg", 0.02),
    "vitaminB12": ("\u00b5g", 0.1), "folate": ("\u00b5g", 0),
    "pantothenicAcid": ("mg", 0.08), "biotin": ("\u00b5g", 0.4),
    "vitaminC": ("mg", 0),
}


class SalmonVinegarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foods = {
            p.name: json.loads(p.read_text(encoding="utf-8"))
            for p in (ROOT / "Foods").glob("*.json")
        }

    def test_touched_records_have_valid_flat_schema(self):
        for filename in ("FarmRaisedSalmon.json", "RiceVinegar.json"):
            with self.subTest(filename=filename):
                food = self.foods[filename]
                self.assertEqual(set(food), {
                    "name", "nutrients", "unitOptions", "attributes",
                    "annotations", "sources",
                })
                self.assertTrue(food["name"])
                names = [n["name"] for n in food["nutrients"]]
                self.assertEqual(len(names), len(set(names)))
                for nutrient in food["nutrients"]:
                    self.assertEqual(set(nutrient), {"name", "unit", "amountPer100g"})
                    self.assertIn(nutrient["unit"], ("g", "mg", "\u00b5g", "kcal"))
                    self.assertTrue(math.isfinite(nutrient["amountPer100g"]))
                    self.assertGreaterEqual(nutrient["amountPer100g"], 0)
                for field in ("attributes", "annotations", "sources"):
                    self.assertTrue(all(isinstance(s, str) and s for s in food[field]))
                    self.assertEqual(len(food[field]), len(set(food[field])))

    def test_exact_mass_units_not_guessed_servings_or_volumes(self):
        for filename in ("FarmRaisedSalmon.json", "RiceVinegar.json"):
            with self.subTest(filename=filename):
                food = self.foods[filename]
                units = food["unitOptions"]
                self.assertEqual(len(units), 3)
                self.assertEqual(
                    [(u["unitFullName"], u["unitAbbreviation"]) for u in units],
                    [("gram", "g"), ("ounce", "oz"), ("pound", "lb")],
                )
                for unit in units:
                    self.assertEqual(set(unit), {
                        "unitFullName", "unitAbbreviation", "portionInGrams",
                    })
                    self.assertTrue(math.isfinite(unit["portionInGrams"]))
                    self.assertGreater(unit["portionInGrams"], 0)
                gram, ounce, pound = (Decimal(str(u["portionInGrams"])) for u in units)
                self.assertEqual(gram, 1)
                self.assertEqual(ounce, Decimal("28.349523125"))
                self.assertEqual(pound, Decimal("453.59237"))
                self.assertEqual(16 * ounce, pound)
                citation = next(s for s in food["sources"] if NIST_URL in s)
                self.assertIn("28.349523125 g", citation)
                self.assertIn("453.59237 g exactly", citation)
                self.assertIn("mass", citation)
        salmon = self.foods["FarmRaisedSalmon.json"]
        self.assertEqual(salmon["name"], "Farm raised salmon")
        self.assertEqual(salmon["annotations"], ["foundation"])
        self.assertIn(
            "Fish, salmon, Atlantic, farm raised, raw via Foundation Foods",
            salmon["sources"][0],
        )
        self.assertIn("/food/2684441", salmon["sources"][0])
        self.assertTrue(any("1 RACC = 115 g" in s for s in salmon["sources"]))

    def test_rice_vinegar_numeric_source_values_and_unknown_omission(self):
        food = self.foods["RiceVinegar.json"]
        actual = {n["name"]: (n["unit"], n["amountPer100g"]) for n in food["nutrients"]}
        self.assertEqual(actual, RICE_VALUES)
        self.assertEqual(food["name"], "Rice vinegar")
        self.assertEqual(food["annotations"], ["mext"])
        self.assertEqual(food["attributes"], ["vegetarian", "vegan"])
        self.assertIn("SEASONINGS AND SPICES/Vinegar/rice vinegar", food["sources"][0])
        self.assertIn("Supplement 2023", food["sources"][0])
        self.assertIn(MEXT_URL, food["sources"][0])
        # MEXT reports trace/missing/estimated entries, not numeric zeros, for these.
        self.assertTrue({
            "sugar", "copper", "selenium", "vitaminE", "fiber",
            "vitaminD", "vitaminK", "saturatedFat", "transFat",
        }.isdisjoint(actual))

    def test_compiler_preserves_source_records_and_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            outputs = [Path(directory) / name for name in ("first.json", "second.json")]
            for output in outputs:
                subprocess.run(
                    [sys.executable, str(ROOT / "Scripts" / "compile_json.py"),
                     str(output), "v39"], cwd=ROOT, check=True,
                )
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
            compiled = json.loads(outputs[0].read_text(encoding="utf-8"))
            self.assertEqual(set(compiled), {"version", "foods"})
            self.assertEqual(compiled["version"], "v39")
            self.assertEqual(
                compiled["foods"], [self.foods[name] for name in sorted(self.foods)],
            )
            names = [f["name"].casefold() for f in compiled["foods"]]
            self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
