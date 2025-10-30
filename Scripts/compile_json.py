import json
import glob
import sys

# Get output filename and version from command line arguments
output_file = sys.argv[1] if len(sys.argv) > 1 else "FoodData.json"
version = sys.argv[2] if len(sys.argv) > 2 else "v1"

# List all JSON files in the directory
json_files = glob.glob("Foods/*.json")
foods = []

for file in json_files:
    with open(file, 'r') as f:
        data = json.load(f)
        foods.append(data)

# Create the output structure with version and foods fields
output_data = {
    "version": version,
    "foods": foods
}

# Save the combined JSON file
with open(output_file, "w") as outfile:
    json.dump(output_data, outfile, indent=4)
