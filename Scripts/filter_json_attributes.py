import json
import glob

def extract_food_names(input_files, output_file):
    """
    Extracts the names of all foods from a list of JSON files and writes them to a new JSON file.

    :param input_files: List of input JSON file paths.
    :param output_file: Path to the output JSON file.
    """
    food_names = []

    for file in input_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                if "name" in data:
                    food_names.append(data["name"])
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file {file}: {e}")

    with open(output_file, "w") as outfile:
        json.dump(food_names, outfile, indent=4)

if __name__ == "__main__":
    # List all JSON files in the directory (go up one level to find Foods folder)
    json_files = glob.glob("../Foods/*.json")

    # Output file name
    output_file_name = "FoodNames.json"

    # Call the function to extract food names
    extract_food_names(json_files, output_file_name)

    print(f"List of food names has been saved to {output_file_name}")
