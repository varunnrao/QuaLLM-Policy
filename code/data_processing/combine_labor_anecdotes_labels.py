import os
import json
import csv
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Get input and output folders from environment variables
INPUT_FOLDER = os.getenv('INPUT_FOLDER')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')


def process_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Exclude category 4
    if data['labor_category'] == 4:
        return None

    # Correct the subreddit name if it's "Ask"
    if data['subreddit_name'] == 'Ask':
        data['subreddit_name'] = 'AskLawyer'

    return data


def combine_json_to_csv(input_subdir, output_subdir):
    os.makedirs(output_subdir, exist_ok=True)

    all_data = []
    json_files = [f for f in os.listdir(input_subdir) if f.endswith('.json')]

    for json_file in tqdm(json_files, desc=f"Processing {os.path.basename(input_subdir)}"):
        file_path = os.path.join(input_subdir, json_file)
        data = process_json_file(file_path)
        if data:
            all_data.append(data)

    if all_data:
        output_file = os.path.join(output_subdir, f"{os.path.basename(input_subdir)}.csv")
        fieldnames = ['subreddit_name', 'key', 'quote', 'summary', 'labor_category']

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_data:
                writer.writerow(row)

        print(f"Created {output_file}")
    else:
        print(f"No valid data found in {input_subdir}")


def main():
    if not os.path.exists(INPUT_FOLDER):
        print(f"Input folder {INPUT_FOLDER} does not exist.")
        return

    for subdir in os.listdir(INPUT_FOLDER):
        input_subdir = os.path.join(INPUT_FOLDER, subdir)
        if os.path.isdir(input_subdir):
            output_subdir = os.path.join(OUTPUT_FOLDER, subdir)
            combine_json_to_csv(input_subdir, output_subdir)


if __name__ == "__main__":
    main()