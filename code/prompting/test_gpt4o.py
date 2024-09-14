import os
from openai import AzureOpenAI
from pydantic import BaseModel
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env(key, default=None, var_type=str):
    value = os.getenv(key, default)
    if value is None:
        return None
    if var_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    return var_type(value)

client = AzureOpenAI(
    api_key=get_env('AZURE_OPENAI_API_KEY'),
    api_version=get_env('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=get_env('AZURE_OPENAI_ENDPOINT')
)

deployment_name = get_env('DEPLOYMENT_NAME')

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.beta.chat.completions.parse(
    model=deployment_name, # replace with the model deployment name of your gpt-4o 2024-08-06 deployment
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
    ],
    response_format=CalendarEvent,
)

event = completion.choices[0].message.parsed

# print(event)
print(json.dumps(event.model_dump(), indent=4))
