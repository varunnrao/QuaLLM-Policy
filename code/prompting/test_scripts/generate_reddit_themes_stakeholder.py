#!/usr/bin/env python
# coding: utf-8

# In[37]:


import os
import json
from openai import AzureOpenAI

def load_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def extract_content(data):
    content = []
    
    def parse_item(item):
        if 'title' in item['data'] and item['data']['title']:
            content.append(f"title: {item['data']['title']}")
        if 'selftext' in item['data'] and item['data']['selftext']:
            content.append(f"title: {item['data']['selftext']}")
        if 'body' in item['data'] and item['data']['body']:
            content.append(f"comment: {item['data']['body']}")
        if 'replies' in item['data'] and item['data']['replies']:
            for reply in item['data']['replies']['data']['children']:
                parse_item(reply)
    
    for listing in data:
        for child in listing['data']['children']:
            parse_item(child)
    
    return '\n'.join(content)

def generate_output(prompt, reddit_data_str, client, deployment_name):
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": reddit_data_str}
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
    prompt_file_path = "prompts/prompt_stakeholder_reddit.txt"
    
    
    stakeholder = "artists"
    reddit_data_path = "data/artists/reddit/professional_artists_how_much_has_ai_art_affected_one_year.json"
    
    output_path = "results/artists"
    client = AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    prompt = load_file(prompt_file_path)
    prompt = prompt.replace("<STAKEHOLDER>", stakeholder)

    reddit_data = load_json(reddit_data_path)
    reddit_data_str = extract_content(reddit_data)

    output_content = generate_output(prompt, reddit_data_str, client, deployment_name)
    
    # Ensure output content is valid JSON
    try:
        output_json = json.loads(output_content)
    except json.JSONDecodeError:
        print("Error: Generated output is not valid JSON")
        return

    output_file_path = os.path.join(output_path, os.path.basename(reddit_data_path)+ '_output.json')
    save_json(output_json, output_file_path)

if __name__ == "__main__":
    main()


# In[ ]:




