import os
import json
import csv
from collections import defaultdict
from dotenv import load_dotenv


def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def process_subreddit_data(anecdotes_folder, labels_folder, output_folder):
    log_data = defaultdict(lambda: defaultdict(int))

    for subreddit in os.listdir(anecdotes_folder):
        subreddit_anecdotes_path = os.path.join(anecdotes_folder, subreddit)
        subreddit_labels_path = os.path.join(labels_folder, subreddit)

        if not os.path.isdir(subreddit_anecdotes_path) or not os.path.isdir(subreddit_labels_path):
            continue

        output_subreddit_path = os.path.join(output_folder, subreddit)
        os.makedirs(output_subreddit_path, exist_ok=True)

        output_csv_path = os.path.join(output_subreddit_path, f"{subreddit}_anecdotes_labels.csv")

        with open(output_csv_path, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['subreddit_name', 'key', 'quote', 'summary', 'category'])

            for filename in os.listdir(subreddit_anecdotes_path):
                if filename.endswith('.json'):
                    key = filename.split('-')[1].split('.')[0]
                    anecdotes_file = os.path.join(subreddit_anecdotes_path, filename)
                    labels_file = os.path.join(subreddit_labels_path, f"output-{key}_labels.json")

                    if not os.path.exists(labels_file):
                        print(f"Warning: Labels file not found for {filename}")
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

    return log_data


def write_log_file(log_data, log_folder):
    os.makedirs(log_folder, exist_ok=True)
    log_file_path = os.path.join(log_folder, 'processing_log.txt')

    with open(log_file_path, 'w') as log_file:
        log_file.write("Subreddit Data Processing Log\n")
        log_file.write("=============================\n\n")

        for subreddit, categories in log_data.items():
            log_file.write(f"Subreddit: {subreddit}\n")
            log_file.write("-----------------\n")
            total_anecdotes = sum(categories.values())
            log_file.write(f"Total anecdotes: {total_anecdotes}\n")
            log_file.write("Anecdotes per category:\n")
            for category, count in categories.items():
                log_file.write(f"  Category {category}: {count}\n")
            log_file.write("\n")


def main():
    load_dotenv()

    input_anecdotes_path = os.getenv('INPUT_ANECDOTES_PATH')
    input_labels_path = os.getenv('INPUT_LABELS_PATH')
    output_folder = os.getenv('OUTPUT_FOLDER')

    if not all([input_anecdotes_path, input_labels_path, output_folder]):
        print("Error: Missing environment variables. Please check your .env file.")
        return

    log_data = process_subreddit_data(input_anecdotes_path, input_labels_path, output_folder)
    write_log_file(log_data, os.path.join(output_folder, 'logs'))

    print("Processing complete. Check the output folder for CSV files and the logs folder for the summary.")


if __name__ == "__main__":
    main()