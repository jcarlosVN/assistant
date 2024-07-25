from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def upload_file(file):
    file = client.files.create(file=open(file,'rb'), purpose='assistants')
    return file

def vector_store(file):
    vector_store = client.beta.vector_stores.create(name=f"vector_store_{file}")
    file_paths = [file]
    file_streams = [open(path, "rb") for path in file_paths]
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id,
    files=file_streams
    )
    print(file_batch.status)
    print(file_batch.file_counts)
    return vector_store.id

def get_current_temperature(location):
    """Get the current temperature in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "30000"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "200"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "300"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_temperature",
            "description": "Get the current temperature in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        },
    }
]
