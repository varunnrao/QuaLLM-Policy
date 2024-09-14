import os
import csv
from collections import defaultdict
from tqdm import tqdm


def process_subreddit_data(folder_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    subreddit_files = defaultdict(dict)
    for file in csv_files:
        subreddit, file_type = file.rsplit('_', 1)
        file_type = file_type.split('.')[0]  # Remove .csv extension
        subreddit_files[subreddit][file_type] = file

    print(f"Processing {len(subreddit_files)} subreddits...")
    for subreddit, files in tqdm(subreddit_files.items(), desc="Subreddits"):
        try:
            process_subreddit(folder_path, subreddit, files.get('submissions'), files.get('comments'), output_folder)
        except Exception as e:
            print(f"Error processing subreddit {subreddit}: {str(e)}")


def process_subreddit(folder_path, subreddit, submissions_file, comments_file, output_folder):
    submissions = read_submissions(os.path.join(folder_path, submissions_file)) if submissions_file else {}
    comments = read_comments(os.path.join(folder_path, comments_file)) if comments_file else defaultdict(list)

    # Combine submissions and comments
    combined_data = {}

    # Process submissions
    for submission_id, submission in submissions.items():
        combined_data[submission_id] = {
            'id': submission_id,
            'title': submission['title'],
            'selftext': submission['selftext'],
            'body': ' '.join(comments.get(submission_id, []))
        }

    # Process comments without matching submissions
    for comment_id in comments:
        if comment_id not in combined_data:
            combined_data[comment_id] = {
                'id': comment_id,
                'title': '',
                'selftext': '',
                'body': ' '.join(comments[comment_id])
            }

    # Write combined data to output file
    output_file = os.path.join(output_folder, f"{subreddit}_llm.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'title', 'selftext', 'body'])
        for data in combined_data.values():
            if is_valid_content(data['selftext']) or is_valid_content(data['body']):
                writer.writerow([
                    data['id'],
                    data['title'],
                    data['selftext'],
                    data['body']
                ])


def read_submissions(file_path):
    submissions = {}
    total_rows = sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='replace'))
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader((line.replace('\0', '') for line in f))
        for row_num, row in tqdm(enumerate(reader, 1), total=total_rows, desc="Reading submissions", leave=False):
            try:
                score, created_utc, title, id, author, permalink, selftext = row
                submissions[id] = {
                    'title': title,
                    'selftext': selftext if is_valid_content(selftext) else ''
                }
            except ValueError as e:
                print(f"Error reading row {row_num} in {file_path}: {str(e)}")
    return submissions


def read_comments(file_path):
    comments = defaultdict(list)
    total_rows = sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='replace'))
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader((line.replace('\0', '') for line in f))
        for row_num, row in tqdm(enumerate(reader, 1), total=total_rows, desc="Reading comments", leave=False):
            try:
                score, created_utc, author, permalink, link_id, body = row
                submission_id = link_id[3:]  # Remove 't3_' prefix
                if is_valid_content(body):
                    comments[submission_id].append(body)
            except ValueError as e:
                print(f"Error reading row {row_num} in {file_path}: {str(e)}")
    return comments


def is_valid_content(text):
    if text in ['[removed]', '[deleted]', '']:
        return False
    return len(text.split()) >= 5


def main():
    input_folder = ''
    output_folder = ''
    process_subreddit_data(input_folder, output_folder)


if __name__ == "__main__":
    main()