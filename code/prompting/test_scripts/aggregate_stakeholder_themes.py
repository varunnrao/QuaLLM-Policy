import os
import json
from openai import AzureOpenAI

def load_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def load_json_files(directory):
    consolidated_data = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                consolidated_data.extend(data)
    return json.dumps(consolidated_data, indent=2)

def generate_output(prompt, input_data, client, deployment_name):
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_data}
        ]
    )
    return response.choices[0].message.content.strip()

def main():
    api_key = ""
    api_version = ""
    azure_endpoint = ""
    deployment_name = ""
    
    stakeholder = "artists"
    prompt_file_path = "prompts/prompt_aggregation_themes.txt"
    input_directory = "results/artists"
    output_directory = "results/artists/aggregated"
    
    client = AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    prompt = load_file(prompt_file_path)
    prompt = prompt.replace("<STAKEHOLDER>", stakeholder)
    consolidated_input = load_json_files(input_directory)

    output_content = generate_output(prompt, consolidated_input, client, deployment_name)
    
    output_file_path = os.path.join(output_directory, stakeholder+"_"+'consolidated_output.txt')
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(output_content)

    print(f"Analysis complete. Output saved to {output_file_path}")

if __name__ == "__main__":
    main()