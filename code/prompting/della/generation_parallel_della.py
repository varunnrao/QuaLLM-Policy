import os
import json
import pandas as pd
import logging
import time
import random
from openai import OpenAI
from multiprocessing import Pool
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, Field
from typing import List


class QuoteSummary(BaseModel):
    quote: str
    summary: str

class AIImpactAnalysis(BaseModel):
    anecdotes: List[QuoteSummary]
    media_reports: List[QuoteSummary]
    opinions: List[QuoteSummary]
    other: List[QuoteSummary]



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenAI client configuration
client = OpenAI(
    api_key="token-varun",
    base_url = "http://localhost:49437/v1"
)

# Global variables
POOL_SIZE = 15
DEPLOYMENT_NAME = 'meta-llama/Meta-Llama-3.1-70B-Instruct'
MAX_RETRIES = 5
MIN_RETRY_WAIT = 1
MAX_RETRY_WAIT = 60


def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT, max=MAX_RETRY_WAIT),
    retry=retry_if_exception_type(Exception)
)
def make_api_call(messages):
    try:
        return client.beta.chat.completions.parse(
            model=DEPLOYMENT_NAME,
            response_format=AIImpactAnalysis,
            messages=messages,
            max_tokens=4096
        )
    except Exception as e:
        logging.warning(f"API call failed: {str(e)}. Retrying...")
        raise


def process_row(args):
    file_path, row, output_dir = args
    subreddit = os.path.basename(file_path).split('_')[0]
    system_prompt = read_file('')

    formatted_submission = {
        "Submission Title": row['title'],
        "Submission Body": row['selftext'],
        "Comments": row['body'],
        "ID": row['id']
    }

    user_prompt = json.dumps(formatted_submission, default=str)

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        output = make_api_call(messages)
        output = output.choices[0].message.parsed

        output_subdir = os.path.join(output_dir, subreddit)
        os.makedirs(output_subdir, exist_ok=True)
        output_path = os.path.join(output_subdir, f'output-{row["id"]}.json')

        with open(output_path, 'w') as file:
            json.dump(output.model_dump(), file, indent=4)

        logging.info(f"Successfully processed and saved output for row {row['id']} in {output_path}")
    except Exception as e:
        logging.error(f"Error processing row {row['id']} in {file_path}: {str(e)}")

def process_file(file_path, output_dir):
    df = pd.read_csv(file_path)
    with Pool(POOL_SIZE) as pool:
        args = [(file_path, row, output_dir) for _, row in df.iterrows()]
        list(tqdm(pool.imap_unordered(process_row, args), total=len(df),
                  desc=f"Processing {os.path.basename(file_path)}"))

def main(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('_llm.csv')]
    total_files = len(csv_files)

    for i, csv_file in enumerate(csv_files, 1):
        file_path = os.path.join(input_dir, csv_file)
        logging.info(f"Processing file {i} of {total_files}: {csv_file}")
        process_file(file_path, output_dir)
        logging.info(f"Completed file {i} of {total_files}: {csv_file}")
        logging.info(f"Files remaining: {total_files - i}")

        time.sleep(random.uniform(1, 5))

if __name__ == '__main__':
    input_directory = ''
    output_directory = ''
    main(input_directory, output_directory)