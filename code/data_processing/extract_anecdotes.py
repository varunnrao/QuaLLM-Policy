import os
import json
import shutil
from pathlib import Path
from multiprocessing import Pool
from dotenv import load_dotenv
from typing import Dict, Any, Iterator


def load_env_variables() -> Dict[str, Any]:
    load_dotenv()
    return {
        'INPUT_FOLDER': Path(os.getenv('INPUT_FOLDER', '')),
        'OUTPUT_FOLDER': Path(os.getenv('OUTPUT_FOLDER', '')),
        'NUM_PROCESSES': int(os.getenv('NUM_PROCESSES', '100'))
    }


def process_file(file_path: Path) -> None:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        anecdotes = data.get('anecdotes', [])
        if not anecdotes:
            return

        output_data = {'anecdotes': anecdotes}

        relative_path = file_path.relative_to(config['INPUT_FOLDER'])
        output_path = config['OUTPUT_FOLDER'] / relative_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Processed: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def find_json_files(folder: Path) -> Iterator[Path]:
    for file_path in folder.rglob('*.json'):
        yield file_path


def main() -> None:
    input_folder = config['INPUT_FOLDER']
    output_folder = config['OUTPUT_FOLDER']

    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True)

    with Pool(config['NUM_PROCESSES']) as pool:
        for _ in pool.imap_unordered(process_file, find_json_files(input_folder)):
            pass


if __name__ == "__main__":
    config = load_env_variables()
    main()