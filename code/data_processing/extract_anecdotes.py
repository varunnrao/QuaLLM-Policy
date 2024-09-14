import os
import json
import shutil
from pathlib import Path
from multiprocessing import Pool
from dotenv import load_dotenv
from typing import Dict, Any, List
from tqdm import tqdm


def load_env_variables() -> Dict[str, Any]:
    load_dotenv()
    return {
        'INPUT_FOLDER': Path(os.getenv('INPUT_FOLDER', '')),
        'OUTPUT_FOLDER': Path(os.getenv('OUTPUT_FOLDER', '')),
        'NUM_PROCESSES': int(os.getenv('NUM_PROCESSES', '4'))
    }


def process_file(args: tuple) -> None:
    file_path, output_folder = args
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        anecdotes = data.get('anecdotes', [])
        if not anecdotes:
            return

        output_data = {'anecdotes': anecdotes}

        relative_path = file_path.relative_to(config['INPUT_FOLDER'])
        output_path = output_folder / relative_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def process_folder(folder: Path) -> None:
    json_files = list(folder.rglob('*.json'))

    with Pool(config['NUM_PROCESSES']) as pool:
        args = [(file, config['OUTPUT_FOLDER']) for file in json_files]
        list(tqdm(pool.imap_unordered(process_file, args), total=len(json_files), desc=f"Processing {folder.name}",
                  leave=False))


def main() -> None:
    input_folder = config['INPUT_FOLDER']
    output_folder = config['OUTPUT_FOLDER']

    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True)

    main_folders = [f for f in input_folder.iterdir() if f.is_dir()]

    for folder in tqdm(main_folders, desc="Processing main folders"):
        process_folder(folder)


if __name__ == "__main__":
    config = load_env_variables()
    main()