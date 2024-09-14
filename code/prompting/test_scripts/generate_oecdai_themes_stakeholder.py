import os
from openai import AzureOpenAI

def load_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_json(data, file_path):
    import json
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def generate_output(prompt, input_data, client, deployment_name):
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_data}
        ]
    )
    response_content = response.choices[0].message.content
    # Remove the ```json block if present
    if response_content.startswith("```json"):
        response_content = response_content[7:]
    if response_content.endswith("```"):
        response_content = response_content[:-3]
    return response_content.strip()

def main():
    api_key = ""
    api_version = ""
    azure_endpoint = ""
    deployment_name = ""
    prompt_file_path = "prompts/prompt_stakeholder_oecd.txt"
    
    stakeholder = "doctors"
    input_data_path = "data/doctors/oecd-ai/Will AI replace radiologists or make them more efficient.txt"
    output_path = "results/doctors"
    client = AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    prompt = load_file(prompt_file_path)
    prompt = prompt.replace("<STAKEHOLDER>", stakeholder)

    input_data = load_file(input_data_path)

    output_content = generate_output(prompt, input_data, client, deployment_name)
    
    # Ensure output content is valid JSON
    try:
        import json
        output_json = json.loads(output_content)
    except json.JSONDecodeError:
        print("Error: Generated output is not valid JSON")
        return

    output_file_path = os.path.join(output_path, os.path.basename(input_data_path) + '_output.json')
    save_json(output_json, output_file_path)

if __name__ == "__main__":
    main()