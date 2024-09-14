import os
from openai import OpenAI
from pydantic import BaseModel
import json

client = OpenAI(
    api_key="token-varun",
    base_url = "http://localhost:49437/v1"
)

deployment_name = 'meta-llama/Meta-Llama-3.1-70B-Instruct'

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.chat.completions.create(
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
