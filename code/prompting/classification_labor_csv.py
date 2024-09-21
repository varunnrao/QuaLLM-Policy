import os
import json
import csv
import logging
from logging.handlers import RotatingFileHandler
import time
from openai import AzureOpenAI
from multiprocessing import Pool
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CategoryResponse(BaseModel):
    category: int


# Function to get environment variables with type conversion
def get_env(key, default=None, var_type=str):
    value = os.getenv(key, default)
    if value is None:
        return None
    if var_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    return var_type(value)


# OpenAI client configuration
client = AzureOpenAI(
    api_key=get_env('AZURE_OPENAI_API_KEY'),
    api_version=get_env('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=get_env('AZURE_OPENAI_ENDPOINT')
)

# Global variables
POOL_SIZE = get_env('POOL_SIZE', 100, int)
DEPLOYMENT_NAME = get_env('DEPLOYMENT_NAME')
MAX_RETRIES = get_env('MAX_RETRIES', 5, int)
MIN_RETRY_WAIT = get_env('MIN_RETRY_WAIT', 1, int)
MAX_RETRY_WAIT = get_env('MAX_RETRY_WAIT', 60, int)


# Configure logging
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
            response_format=CategoryResponse,
            messages=messages,
            max_tokens=4096
        )
    except Exception as e:
        logging.warning(f"API call failed: {str(e)}. Retrying...")
        raise


def process_row(args):
    row, system_prompt, output_dir = args
    try:
        subreddit_name, key, quote, summary, _ = row

        input_json = json.dumps({
            "subreddit_name": subreddit_name,
            "quote": quote,
            "summary": summary
        })

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_json}
        ]

        output = make_api_call(messages)
        labor_category = output.choices[0].message.parsed.category

        result = {
            "subreddit_name": subreddit_name,
            "key": key,
            "quote": quote,
            "summary": summary,
            "labor_category": labor_category
        }

        output_subdir = os.path.join(output_dir, subreddit_name)
        os.makedirs(output_subdir, exist_ok=True)
        output_file = os.path.join(output_subdir, f'output-{subreddit_name}-{key}_category_1.json')

        with open(output_file, 'w') as file:
            json.dump(result, file, indent=4)

        logging.info(f"Successfully processed and saved output for {subreddit_name}-{key}")
    except Exception as e:
        logging.error(f"Error processing row {row}: {str(e)}")


def process_csv(csv_file, system_prompt, output_dir):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        rows = list(reader)

    total_rows = len(rows)
    logging.info(f"Processing {total_rows} rows in {csv_file}")

    with Pool(POOL_SIZE) as pool:
        args = [(row, system_prompt, output_dir) for row in rows]
        list(tqdm(pool.imap_unordered(process_row, args), total=total_rows,
                  desc=f"Processing rows in {csv_file}"))

    logging.info(f"Completed processing {csv_file}")


def main(input_dir, output_dir):
    setup_logging()
    system_prompt = read_file(get_env('SYSTEM_PROMPT_PATH'))

    subdirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]

    total_subdirs = len(subdirs)
    logging.info(f"Found {total_subdirs} subdirectories to process")

    for subdir in tqdm(subdirs, desc="Processing subdirectories"):
        subdir_path = os.path.join(input_dir, subdir)
        csv_files = [f for f in os.listdir(subdir_path) if f.endswith('category_1.csv')]

        if not csv_files:
            logging.warning(f"No matching CSV file found in {subdir_path}")
            continue

        csv_file = os.path.join(subdir_path, csv_files[0])
        process_csv(csv_file, system_prompt, output_dir)

    logging.info("All subdirectories processed")


if __name__ == '__main__':
    input_directory = get_env('INPUT_DIRECTORY')
    output_directory = get_env('OUTPUT_DIRECTORY')
    main(input_directory, output_directory)