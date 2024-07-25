from openai import OpenAI
import manage_ids, manage_tools
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def create_assistant_file_search(file, name, instructions):
    vs = manage_tools.vector_store(file)
    new_assistant = client.beta.assistants.create(
        name=name,
        description="file_search",
        instructions=instructions,
        model="gpt-4-1106-preview",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vs]}}
    )
    # save data in assistants_threads_users_db.txt
    json_data = manage_ids.load_data()
    json_data[new_assistant.id] = {'name': new_assistant.name, 'description': new_assistant.description, 'threads': {}}
    manage_ids.save_data(json_data)
    return {"id": new_assistant.id, "name": new_assistant.name, 'description': new_assistant.description}

def create_assistant_funtion_calling(name, instructions, tools):
    new_assistant = client.beta.assistants.create(
    name=name,
    description="funtion_calling",
    instructions=instructions,
    model="gpt-4-1106-preview",
    tools=tools
    )
    # save data in assistants_threads_users_db.txt
    json_data = manage_ids.load_data()
    json_data[new_assistant.id] = {'name': new_assistant.name, 'description': new_assistant.description, 'threads': {}}
    manage_ids.save_data(json_data)
    return {"id": new_assistant.id, "name": new_assistant.name, 'description': new_assistant.description}
