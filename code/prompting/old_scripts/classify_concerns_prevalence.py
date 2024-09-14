from multiprocessing import Pool
import os
import math
import pandas as pd
from openai import AzureOpenAI
import time
import ast
import glob

client = AzureOpenAI(
    api_key="",
    api_version="",
    azure_endpoint=""
)

deployment_name = ''  # This will correspond to the custom name you chose for your deployment when you deployed a model.

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def generate_concerns_list(batch):
    concerns = [f"{i+1}. {row['title'].strip()}: {row['description'].strip()}" for i, row in batch.iterrows()]
    return '\n'.join(concerns)

def add_quotes_if_needed(s):
    # Check if the string is a single character and not already quoted
    if len(s) == 1 and not (s.startswith("'") and s.endswith("'")):
        return "'" + s + "'"
    return s

def call_openai_api(batch_df, start_index, output_folder, system_prompt):
    global client
    global deployment_name

    # Concatenate title and description into a single string for each row, separated by a newline
    print("processing:", start_index, len(batch_df))
    concatenated_strings = generate_concerns_list(batch_df)

    # Save the response to a .txt file
    file_path = f"{output_folder}/batch_{start_index}_{start_index + len(batch_df) - 1}.txt"
    if(os.path.exists(file_path)):
        print(file_path, 'already exists and skipping making another LLM call')
    else:
        success = False
        while not success:
            try:
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": concatenated_strings}
                    ],
                    max_tokens=4096
                )

                output = response.choices[0].message.content

                cleaned_str = output.strip("`{} \n\t")
                pairs = cleaned_str.split(',')
                categories = [pair.split(':')[1].strip(" '") for pair in pairs]
                num_lines = len(concatenated_strings.split("\n"))
        
                valid_categories = {'A', 'B', 'C', 'D', 'E', 'F'}
                if (not all(item in valid_categories for item in categories)) or (len(categories) != num_lines):
                    print("incorrect lines or categories in output")
                    continue                
    
                with open(file_path, 'w') as file:
                    file.write(output)
    
                success = True  # API call was successful
            except Exception as e:
                print(f"API call failed: {e}. Retrying in 60 seconds...")
                time.sleep(60)  # Wait for 60 seconds before retrying   
    

def process_batches_in_parallel(df, output_folder, system_prompt, batch_size=500, pool_size=10):
    
    num_batches = math.ceil(len(df) / batch_size)
    # import pdb; pdb.set_trace()
    batches = [(df.iloc[batch_num * batch_size: (batch_num + 1) * batch_size], batch_num * batch_size, output_folder, system_prompt) 
               for batch_num in range(num_batches)]

    with Pool(pool_size) as pool:
        pool.starmap(call_openai_api, batches)

def update_dataframe_from_output(df, output_folder):
    df['prevalence_category'] = None
    file_list = sorted(glob.glob(os.path.join(output_folder, '*.txt')))
    for file_name in file_list:
        file_path = os.path.join(output_folder, file_name)
        with open(file_path, 'r') as file:

            # Read the content of the file
            file_content = file.read()

            # Process the file content: Add quotes around the characters
            processed_content = ''.join(["'" + ch + "'" if ch.isalpha() else ch for ch in file_content])
            # processed_content = ''.join([add_quotes_if_needed(ch) if ch.isalpha() else ch for ch in file_content])

            # Convert the processed string to a dictionary
            prevalence_category_dict = ast.literal_eval(processed_content)

            # Update the DataFrame
            for row_index, category in prevalence_category_dict.items():
                df.at[row_index - 1, 'prevalence_category'] = category
    
    # display aggregate percentages
    category_counts = df['prevalence_category'].value_counts()
    # Calculate the total number of rows
    total_rows = len(df)    
    # Calculate the percentage of each category
    category_percentages = (category_counts / total_rows) * 100    
    # Output the results
    print("Category Counts:\n", category_counts)
    print("\nTotal Number of Rows:", total_rows)
    print("\nCategory Percentages:\n", category_percentages)  
    return df

# Example usage
# Assuming `df` is your original DataFrame with 'title' and 'description' columns
# df = pd.DataFrame(...)  # your DataFrame here
# output_folder = "path_to_output_folder"  # Define the output folder path
# process_batches_in_parallel(df, output_folder)
# updated_df = update_dataframe_from_output(df, output_folder)
# print(updated_df)

if(__name__ == '__main__'):

    # system_prompt = read_file('')
    # df = pd.read_csv('')
    # output_folder = ""
    
    # process_batches_in_parallel(df, output_folder, system_prompt)

    # df = pd.read_csv('')
    # df = update_dataframe_from_output(df, '')
    # output_file_path = ''
    # df.to_csv(output_file_path, index=False)
    