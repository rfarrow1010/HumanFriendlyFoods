import json
import glob

# List all JSON files in the directory
json_files = glob.glob("Foods/*.json")
combined_data = []

for file in json_files:
    with open(file, 'r') as f:
        data = json.load(f)
        combined_data.append(data)

# Save the combined JSON file
with open("FoodData.json", "w") as outfile:
    json.dump(combined_data, outfile, indent=4)
