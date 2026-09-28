"""Scoped regression gates for curated USDA meat variants and flat compilation."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from import_meat_variants import ROOT, VARIANTS, generate


FOODS_DIR = ROOT / "Foods"
EXPECTED_MACROS = {
    "173110": (152, 20.85, 7.0),
    "174699": (187, 19.46, 11.4),
    "173975": (217, 19.8, 15.21),
    "171474": (172, 20.85, 9.25),
}
EXISTING_NAMES = {
    "EightyPercentGroundBeef.json": "80% lean ground beef",
    "NinetyPercentGroundBeef.json": "Ninety percent ground beef",
    "RibeyeSteak.json": "Ribeye steak",
    "ChickenBreast.json": "Chicken breast",
}


class MeatVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foods = {p.name: json.loads(p.read_text(encoding="utf-8"))
                     for p in FOODS_DIR.glob("*.json")}

    def test_unique_names_and_existing_references(self):
        names = [food["name"] for food in self.foods.values()]
        self.assertEqual(len(names), len(set(name.casefold() for name in names)))
        for filename, name in EXISTING_NAMES.items():
            self.assertEqual(self.foods[filename]["name"], name)

    def test_provenance_and_nutrition(self):
        ids = {}
        for filename, food in self.foods.items():
            for citation in food.get("sources", []):
                for fdc_id in re.findall(r"/food/(\d+)\b", citation):
                    ids.setdefault(fdc_id, set()).add(filename)
        for fdc_id, (description, name, filename, _) in VARIANTS.items():
            with self.subTest(fdc_id=fdc_id):
                food = self.foods[filename]
                self.assertEqual(food["name"], name)
                self.assertEqual(ids[fdc_id], {filename})
                self.assertEqual(food["annotations"], ["srLegacy"])
                self.assertEqual(len(food["sources"]), 1)
                self.assertIn(description + " via SR Legacy", food["sources"][0])
                self.assertTrue(description.endswith(", raw"))
                nutrients = {n["name"]: n for n in food["nutrients"]}
                self.assertEqual(len(nutrients), len(food["nutrients"]))
                self.assertEqual(
                    tuple(nutrients[n]["amountPer100g"] for n in
                          ("calories", "protein", "fat")),
                    EXPECTED_MACROS[fdc_id],
                )
                self.assertEqual(
                    [nutrients[n]["unit"] for n in ("calories", "protein", "fat")],
                    ["kcal", "g", "g"],
                )
                self.assertEqual(food["unitOptions"][0]["portionInGrams"], 1)
                self.assertTrue(all(u["portionInGrams"] > 0 for u in food["unitOptions"]))

    def test_fat_significant_variants_remain_separate(self):
        ground = [self.foods[n] for n in (
            "EightyPercentGroundBeef.json", "NinetyPercentGroundBeef.json",
            "NinetyThreePercentGroundBeef.json")]
        fats = [{n["name"]: n["amountPer100g"] for n in f["nutrients"]}["fat"]
                for f in ground]
        self.assertGreater(fats[0], fats[1])
        self.assertGreater(fats[1], fats[2])
        def fat(filename):
            return next(n["amountPer100g"] for n in self.foods[filename]["nutrients"]
                        if n["name"] == "fat")
        self.assertGreater(fat("RibeyeSteak.json"), fat("GrassFedRibeyeSteakLeanAndFat.json"))
        self.assertGreater(fat("GrassFedRibeyeSteakLeanAndFat.json"),
                           fat("RibeyeCapSteakChoiceLeanOnly.json"))
        self.assertGreater(fat("ChickenBreastWithSkin.json"), fat("ChickenBreast.json"))

    def test_compilation_is_deterministic_and_flat(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = (Path(directory) / filename for filename in ("a.json", "b.json"))
            for output in (first, second):
                subprocess.run(
                    [sys.executable, str(ROOT / "Scripts" / "compile_json.py"),
                     str(output), "v38"],
                    cwd=ROOT, check=True,
                )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            compiled = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(set(compiled), {"version", "foods"})
            self.assertEqual(compiled["version"], "v38")
            self.assertEqual(len(compiled["foods"]), len(self.foods))
            self.assertEqual(
                {food["name"] for food in compiled["foods"]},
                {food["name"] for food in self.foods.values()},
            )

    def test_import_matches_archive_when_supplied(self):
        # Pass the official archive as the first unittest argument to check reproduction.
        if not hasattr(self, "archive"):
            self.skipTest("USDA CSV archive not supplied")
        for filename, food in generate(self.archive, FOODS_DIR).items():
            self.assertEqual(food, self.foods[filename])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith(".zip"):
        MeatVariantTests.archive = Path(sys.argv.pop(1))
    unittest.main()
