import os
import json
import csv
import time
import logging
from collections import defaultdict
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from tqdm import tqdm


def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'processing_{time.strftime("%Y%m%d-%H%M%S")}.log')

    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    console_handler = logging.StreamHandler()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[file_handler, console_handler]
    )


def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def process_subreddit_data(anecdotes_folder, labels_folder, output_folder):
    log_data = defaultdict(lambda: defaultdict(int))

    subreddits = [subreddit for subreddit in os.listdir(anecdotes_folder)
                  if os.path.isdir(os.path.join(anecdotes_folder, subreddit))
                  and os.path.isdir(os.path.join(labels_folder, subreddit))]

    for subreddit in tqdm(subreddits, desc="Processing subreddits"):
        logging.info(f"Processing subreddit: {subreddit}")

        subreddit_anecdotes_path = os.path.join(anecdotes_folder, subreddit)
        subreddit_labels_path = os.path.join(labels_folder, subreddit)

        output_subreddit_path = os.path.join(output_folder, subreddit)
        os.makedirs(output_subreddit_path, exist_ok=True)

        output_csv_path = os.path.join(output_subreddit_path, f"{subreddit}_anecdotes_labels.csv")

        with open(output_csv_path, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['subreddit_name', 'key', 'quote', 'summary', 'category'])

            json_files = [f for f in os.listdir(subreddit_anecdotes_path) if f.endswith('.json')]
            for filename in tqdm(json_files, desc=f"Processing files in {subreddit}", leave=False):
                key = filename.split('-')[1].split('.')[0]
                anecdotes_file = os.path.join(subreddit_anecdotes_path, filename)
                labels_file = os.path.join(subreddit_labels_path, f"output-{key}_labels.json")

                if not os.path.exists(labels_file):
                    logging.warning(f"Labels file not found for {filename}")
                    continue

                anecdotes_data = load_json(anecdotes_file)
                labels_data = load_json(labels_file)

                for anecdote, category in zip(anecdotes_data['anecdotes'], labels_data['categories']):
                    csvwriter.writerow([
                        subreddit,
                        key,
                        anecdote['quote'],
                        anecdote['summary'],
                        category
                    ])
                    log_data[subreddit][category] += 1

        logging.info(f"Completed processing for subreddit: {subreddit}")

    return log_data


def write_log_file(log_data, log_folder):
    os.makedirs(log_folder, exist_ok=True)
    log_file_path = os.path.join(log_folder, 'processing_summary.txt')

    with open(log_file_path, 'w') as log_file:
        log_file.write("Subreddit Data Processing Summary\n")
        log_file.write("=================================\n\n")

        for subreddit, categories in log_data.items():
            log_file.write(f"Subreddit: {subreddit}\n")
            log_file.write("-----------------\n")
            total_anecdotes = sum(categories.values())
            log_file.write(f"Total anecdotes: {total_anecdotes}\n")
            log_file.write("Anecdotes per category:\n")
            for category, count in categories.items():
                log_file.write(f"  Category {category}: {count}\n")
            log_file.write("\n")

    logging.info(f"Summary log file written to: {log_file_path}")


def main():
    setup_logging()
    load_dotenv()

    input_anecdotes_path = os.getenv('INPUT_ANECDOTES_PATH')
    input_labels_path = os.getenv('INPUT_LABELS_PATH')
    output_folder = os.getenv('OUTPUT_FOLDER')

    if not all([input_anecdotes_path, input_labels_path, output_folder]):
        logging.error("Missing environment variables. Please check your .env file.")
        return

    logging.info("Starting subreddit data processing")
    log_data = process_subreddit_data(input_anecdotes_path, input_labels_path, output_folder)
    write_log_file(log_data, os.path.join(output_folder, 'logs'))

    logging.info("Processing complete. Check the output folder for CSV files and the logs folder for the summary.")


if __name__ == "__main__":
    main()