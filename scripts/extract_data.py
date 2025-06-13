#!/usr/bin/env python3
import json
import sys


def extract_data(file_path):
    try:
        # Read the JSON file
        with open(file_path, "r") as file:
            data = json.load(file)

        # Extract the "data" field
        if "data" in data:
            # The "data" field is itself a JSON string, so we need to parse it
            contest = data["data"]
            contest = contest.replace("\n\n", "@@n@@")
            data_content = json.loads(contest)

            def fix_newlines(obj):
                if isinstance(obj, dict):
                    return {k: fix_newlines(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [fix_newlines(item) for item in obj]
                elif isinstance(obj, str):
                    return obj.replace("@@n@@", "\n\n")
                else:
                    return obj

            data_content = fix_newlines(data_content)

            data["data"] = data_content
            # Pretty print the extracted data
            print(json.dumps(data, indent=2))
        else:
            print("Error: No 'data' field found in the JSON file")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if file path is provided as an argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "test.json"  # Default to test.json if no argument provided

    extract_data(file_path)
