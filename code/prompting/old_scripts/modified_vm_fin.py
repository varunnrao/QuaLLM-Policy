import json
import pandas as pd
import re
import math
import logging
from openai import AzureOpenAI
from multiprocessing import Pool
import time

# global variables
processed_df = pd.read_csv('')
pool_size = 15
deployment_name=''

# openai information
client = AzureOpenAI(
    api_key="",
    api_version="",
    azure_endpoint = ""
    )

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# formatting submission data to format specified in the prompt
def format_submission_data(row, group_key):
    return {
        "Submission Title": row['title'],
        "Submission Body": row['body'],
        "Timestamp": row['created'],
        "Group Key": group_key,
        "Comments": row['comment_body']  # Assuming this is a list of comments
    }

def process_row (idx):
    bad_input, bad_output = 0, 0
    row = processed_df.iloc[idx]
    curr_group_key = row['group_key']
    curr_timestamp = row['first_timestamp']
    system_prompt = read_file('prompt.txt')
    batch_num = math.floor(idx / 1000) + 1

    formatted_submissions = []
    for i in range(1, 6):  
        submission_data = json.loads(row[f'submission_{i}']) if row[f'submission_{i}'] else None
        if submission_data:
            formatted_submission = format_submission_data(submission_data, curr_group_key)
            formatted_submissions.append(formatted_submission)

    user_prompt = json.dumps(formatted_submissions, default=str)  

    total_input_tokens = int(len(system_prompt.split()) + len(user_prompt.split()) * 1.3)
    total_output_tokens = 0
    try:
        response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096
            )
        
        output = response.choices[0].message.content
        total_output_tokens = int(len(output.split()) * 1.3)
        json_objects = re.findall(r'\{.*?\}', output, re.DOTALL)
        for json_str in json_objects:
            try:
                output_json = json.loads(json_str)
                output_json['group_key'] = curr_group_key
                output_json['timestamp'] = curr_timestamp

                with open(f'output/{batch_num}/output-{curr_group_key}.txt', 'a') as file:
                    json.dump(output_json, file, indent=4)
                    file.write("\n")
            except Exception as e:
                bad_output = 1
                with open('bad_outputs.txt', 'a') as file:
                    file.write(curr_group_key + "\n")
                break
    except Exception as e:
        bad_input = 1
        with open('bad_inputs.txt', 'a') as file:
            file.write(curr_group_key + "\n")
    
    logging.info("Finished processing group {idx} in batch {batch_num}")

    return total_input_tokens, total_output_tokens, bad_input, bad_output, curr_group_key  
        
if __name__ == '__main__':
    bad_input_group_keys = []
    bad_output_group_keys = []
    num_groups_processed = 0
    total_input_tokens = 0
    total_output_tokens = 0

    # uncomment for full run
    for i in range(193, int(math.ceil(len(processed_df) / 100))):
        if (i + 1) % 5 == 0:
            print('Sleeping for 1 minute...')
            time.sleep(60)
        start_idx = i * 100 # start at 0, 100, 200, etc.
        end_idx = min((i + 1) * 100, len(processed_df))
        batch_num = (i // 10) + 1 # batch changes every 10 iterations (1000 rows)
        subbatch_num = (i % 10) + 1 # subbatch cycles from 1 to 10 within each batch

    # # just for testing
    # processed_df = processed_df.iloc[3000:3100]
    # for i in range(int(math.ceil(len(processed_df) / 2))):
    #     start_idx = i * 2
    #     end_idx = min((i + 1) * 2, len(processed_df))
    #     batch_num = (i // 5) + 1  # batch changes every 5 iterations (10 rows)
    #     subbatch_num = (i % 5) + 1 # subbatch cycles from 1 to 5 within each batch

        print(f"Starting batch {batch_num}, section {subbatch_num}")
        print(f"Processing groups {start_idx} to {end_idx}...")

        start_time = time.time()
        with Pool(pool_size) as pool:
            result_all = pool.imap_unordered(process_row, range(start_idx, end_idx))

            for result in result_all:
                total_input_tokens += result[0]
                total_output_tokens += result[1]
                if result[2]:
                    bad_input_group_keys.append(result[4])
                if result[3]:
                    bad_output_group_keys.append(result[4])
                num_groups_processed += 1

        end_time = time.time()
        print(f"Elapsed time: {end_time - start_time} seconds")
        print("Total input tokens: ", total_input_tokens)   
        print("Total output tokens: ", total_output_tokens)

        # adding 578 and 31, errors for first 4700 rows
        # need to handle and reprocess rows 4700-4800 (delete corresponding inputs and then rerun otherwise)
        # it will append to existing concerns)
        # need to rerun rows 14100-14200 (delete corresponding inputs and then rerun otherwise)
        # need to rerun rows 19200-19300 (delete corresponding inputs and then rerun otherwise)
        print("The number of groups which resulted in an OpenAI API error is: ", str(1796 + len(bad_input_group_keys)))
        print("The number of groups which didn't yield a valid JSON format as output is: ", str(125 + len(bad_output_group_keys)))
        print("Parallel processing complete.")