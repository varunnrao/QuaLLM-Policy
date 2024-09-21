import os
import csv
from collections import defaultdict
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Get input and output folders from environment variables
INPUT_FOLDER = os.getenv('INPUT_FOLDER')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')

# Define the industry categories and their corresponding subreddits
INDUSTRY_CATEGORIES = {
    'Creatives': [
        'freelanceWriters', 'screenwriting', 'creativewriting', 'Poetry', 'Writers',
        'Writing', 'Journalism', 'Music', 'Musicians', 'ArtistLounge', 'VoiceActing'
    ],
    'Professionals': [
        'AskLawyers', 'Paralegal', 'Nursing', 'Medicine', 'SoftwareEngineering',
        'SoftwareDevelopment', 'DevelopersIndia'
    ],
    'Educators': ['Teachers', 'Education']
}


def read_csv_file(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def write_csv_file(file_path, data, fieldnames):
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def sort_data(data):
    # Sort by subreddit_name and then by labor_category
    return sorted(data, key=lambda x: (x['subreddit_name'], int(x['labor_category'])))


def get_category_counts(data):
    counts = defaultdict(int)
    for row in data:
        counts[int(row['labor_category'])] += 1
    return counts


def combine_csv_files():
    industry_data = defaultdict(list)
    total_counts = defaultdict(int)

    # Process each CSV file in the input folder
    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith('.csv'):
            file_path = os.path.join(INPUT_FOLDER, filename)
            subreddit_name = os.path.splitext(filename)[0]

            # Determine which industry this subreddit belongs to
            industry = next((ind for ind, subs in INDUSTRY_CATEGORIES.items() if subreddit_name in subs), None)

            if industry:
                print(f"Processing {filename} for {industry}")
                data = read_csv_file(file_path)
                industry_data[industry].extend(data)
            else:
                print(f"Skipping {filename} - not in any defined industry")

    # Sort and write the combined data for each industry
    for industry, data in industry_data.items():
        sorted_data = sort_data(data)
        output_file = os.path.join(OUTPUT_FOLDER, f"{industry}.csv")
        write_csv_file(output_file, sorted_data, sorted_data[0].keys())
        print(f"Created {output_file}")

        # Count categories for this industry
        industry_counts = get_category_counts(sorted_data)
        print(f"\nSummary for {industry}:")
        for category in [1, 2, 3]:
            count = industry_counts[category]
            print(f"Category {category}: {count}")
            total_counts[category] += count
        industry_total = sum(industry_counts.values())
        print(f"Total for {industry}: {industry_total}")
        total_counts['total'] += industry_total

    # Print overall summary
    print("\nOverall Summary:")
    for category in [1, 2, 3]:
        print(f"Category {category}: {total_counts[category]}")
    print(f"Total across all industries: {total_counts['total']}")


def main():
    if not os.path.exists(INPUT_FOLDER):
        print(f"Input folder {INPUT_FOLDER} does not exist.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    combine_csv_files()


if __name__ == "__main__":
    main()