import os
import csv
import logging
from dotenv import load_dotenv
from tqdm import tqdm


def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'categorization.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def process_csv_file(input_file, output_folder):
    subreddit = os.path.basename(os.path.dirname(input_file))
    category_files = {}

    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames

        for row in reader:
            category = row['category']
            if category not in category_files:
                output_file = os.path.join(output_folder, f"{subreddit}_anecdotes_category_{category}.csv")
                category_files[category] = open(output_file, 'w', newline='')
                writer = csv.DictWriter(category_files[category], fieldnames=fieldnames)
                writer.writeheader()

            csv.DictWriter(category_files[category], fieldnames=fieldnames).writerow(row)

    # Close all opened files
    for category in category_files:
        category_files[category].close()

    logging.info(f"Processed {subreddit}: Created {len(category_files)} category files")


def main():
    setup_logging()
    load_dotenv()

    input_folder = os.getenv('INPUT_FOLDER')
    if not input_folder:
        logging.error("Missing INPUT_FOLDER environment variable. Please check your .env file.")
        return

    logging.info("Starting subreddit anecdote categorization")

    for subreddit in tqdm(os.listdir(input_folder), desc="Processing subreddits"):
        subreddit_path = os.path.join(input_folder, subreddit)
        if not os.path.isdir(subreddit_path):
            continue

        csv_files = [f for f in os.listdir(subreddit_path) if f.endswith('_anecdotes_labels.csv')]
        if not csv_files:
            logging.warning(f"No CSV file found for subreddit: {subreddit}")
            continue

        input_file = os.path.join(subreddit_path, csv_files[0])
        process_csv_file(input_file, subreddit_path)

    logging.info("Categorization complete. Check the input folder for category-specific CSV files.")


if __name__ == "__main__":
    main()