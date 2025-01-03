import json
import glob

# List all JSON files in the directory
json_files = glob.glob("Foods/*.json")
combined_data = []
print(json_files)

for file in json_files:
    with open(file, 'r') as f:
        print(f"Opening {file}")
        data = json.load(f)
        combined_data.append(data)

# Save the combined JSON file
with open("FoodData.json", "w") as outfile:
    print("Writing file")
    json.dump(combined_data, outfile, indent=4)
