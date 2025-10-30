import json
import glob
import sys

# Get output filename from command line argument, or use default
output_file = sys.argv[1] if len(sys.argv) > 1 else "FoodData.json"

# List all JSON files in the directory
json_files = glob.glob("Foods/*.json")
combined_data = []

for file in json_files:
    with open(file, 'r') as f:
        data = json.load(f)
        combined_data.append(data)

# Save the combined JSON file
with open(output_file, "w") as outfile:
    json.dump(combined_data, outfile, indent=4)
