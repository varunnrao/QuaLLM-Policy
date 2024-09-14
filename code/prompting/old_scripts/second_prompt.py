import os
import time
import pandas as pd
from openai import AzureOpenAI
import multiprocessing
import glob

# OpenAI and Azure configuration
deployment_name = ''
client = AzureOpenAI(
    api_key="",
    api_version="",
    azure_endpoint=""
)

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Read in DataFrame from CSV
df = pd.read_csv('')
df = df.drop('desc', axis=1)
system_prompt = read_file('')

def llm_output(concerns_list, start_index):
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": concerns_list}
        ],
        max_tokens=4096
    )
    output = response.choices[0].message.content
    try:
        cleaned_str = output.strip("`{} \n\t")
        pairs = cleaned_str.split(',')
        categories = [pair.split(':')[1].strip(" '") for pair in pairs]

        valid_categories = {'A', 'B', 'C', 'D', 'E'}
        if not all(item in valid_categories for item in categories):
            raise ValueError("Invalid category detected in the output.")

        num_lines = len(concerns_list.split("\n"))
        if len(categories) != num_lines:
            raise ValueError(f"Length mismatch: Expected {num_lines} lines, got {len(categories)} categories")

        return categories

    except Exception as e:
        print(f"Error in parsing LLM output: {e}")
        with open('error_indices.txt', 'a') as error_file:
            error_file.write(f"Start index {start_index}: {e}\n")
        return None

def generate_concerns_list(batch):
    concerns = [f"{i+1}. {row['title']}: {row['description']}" for i, row in batch.iterrows()]
    return '\n'.join(concerns)

def worker(start, end, batch_data):
    print(f"Processing batch from index {start} to {end-1}...")
    concerns_list = generate_concerns_list(pd.DataFrame(batch_data))
    categories = llm_output(concerns_list, start)
    if categories is not None:
        batch_df = pd.DataFrame({'Index': range(start, end), 'Category': categories})
        batch_df.to_csv(f'output2/batch_output_{start}_{end-1}.csv', index=False)
    return start, categories

def merge_batch_results(df):
    print("Merging batch results into the DataFrame...")
    all_files = glob.glob('batch_output_*.csv')
    for file_name in all_files:
        batch_df = pd.read_csv(file_name)
        for _, row in batch_df.iterrows():
            df.at[row['Index'], 'Category'] = row['Category']

if __name__ == "__main__":
    df['Category'] = pd.Series(dtype='object')
    batch_size = 500
    num_processes = 10

    # Specific batch start indices
    specific_starts = [5500, 7000, 15500, 17000, 17500, 28000, 30500, 37000, 40000, 53500, 70000, 72000, 87500, 89500]
    
    # Create batches, adjusting for the end of the DataFrame
    batches = []
    for start in specific_starts:
        if start < len(df):
            end = min(start + batch_size, len(df))
            batch_data = df.iloc[start:end].to_dict('records')
            batches.append((start, end, batch_data))

    problematic_batches = []
    with multiprocessing.Pool(processes=num_processes) as pool:
        print("Starting multiprocessing...")
        results = pool.starmap(worker, batches)

    for start, categories in results:
        if categories is None:
            problematic_batches.append(start)
    
    # Merge batch results back into the original DataFrame
    merge_batch_results(df)

    # Save the updated DataFrame
    output_file_path = 'final_grouped_data.csv'
    df.to_csv(output_file_path, index=False)
    print(f"Data saved to {output_file_path}")

    if problematic_batches:
        print(f"Problematic batch start indices: {problematic_batches}")
