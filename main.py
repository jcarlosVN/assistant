
from openai import OpenAI
import os
import time
import json
import create_assistant, manage_ids, manage_tools
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

#-----------------------------------------------------

# Función para verificar si existe el thread
def check_if_thread_exists(user, assistant_id):
    json_data = manage_ids.load_data()
    assistant_data = json_data.get(assistant_id, {})
    return assistant_data.get('threads', {}).get(user, None)

# Función para almacenar el thread
def store_thread(user, thread_id, assistant_id):
    json_data = manage_ids.load_data()
    if assistant_id not in json_data:
        json_data[assistant_id] = {'name': "", 'description': "", 'threads': {}}
    json_data[assistant_id]['threads'][user] = thread_id
    manage_ids.save_data(json_data)

def list_assistants():
    json_data = manage_ids.load_data()
    return [{"id": assistant_id, "description": assistant_data["description"], "name": assistant_data["name"]} for assistant_id, assistant_data in json_data.items()]

def assign_assistant():
    existing_assistants = list_assistants()
    if existing_assistants:
        print("Existing Assistants:")
        for i, assistant in enumerate(existing_assistants, 1):
            print(f"{i}. {assistant['name']} ({assistant['description']}) (ID: {assistant['id']})")
        choice = input("Choose an assistant by number: ")
        if choice.isdigit() and 1 <= int(choice) <= len(existing_assistants):
            chosen_assistant = existing_assistants[int(choice) - 1]
            return {"id": chosen_assistant['id'], "name": chosen_assistant['name'],"description": chosen_assistant['description']} #{'id': 'asst_enmisSqv9zFLCz7oA4xz02kW', 'name': 'asistente_alertas', 'description': 'file_search'}
        else:
            print("Invalid choice.")
            return None
    else:
        print("No existing assistants found. Please request to create a new assistant.")
        return None

#-----------------------------------------------------

def create_response(user, question, assistant_id):
    print(assistant_id)
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(assistant_id["id"])

    # Check if there is already a thread_id for the user and assistant
    thread_id = check_if_thread_exists(user, assistant_id["id"])
    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {user} with assistant {assistant_id["name"]}")
        thread = client.beta.threads.create()
        store_thread(user, thread.id, assistant_id["id"])
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {user} with assistant {assistant_id["name"]}")
    thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )
    new_message = run_assistant(thread, assistant)
    return new_message

def run_assistant(thread, assistant):

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(run.status)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    return new_message


#-----------------------------------------------------

def create_response_fcalling(user, question, assistant_id):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(assistant_id["id"])

    # Check if there is already a thread_id for the user and assistant
    thread_id = check_if_thread_exists(user, assistant_id["id"])
    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {user} with assistant {assistant_id["name"]}")
        thread = client.beta.threads.create()
        store_thread(user, thread.id, assistant_id["id"])
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {user} with assistant {assistant_id["name"]}")
    thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )

    value1, value2 = run_assistant_fcalling(thread, assistant)
    if value2 == "completed":
        return value1
    elif value2 == "requires_action":
        run = value1

    tool_outputs = []

    # Loop through each tool in the required action section
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "get_current_temperature":
            arguments = json.loads(tool_call.function.arguments)
            output = arguments['location']
            print(arguments, output)
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": manage_tools.get_current_temperature(output)
            })
        elif tool_call.function.name == "get_rain_probability":
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": "0.06"
            })

    # Submit all tool outputs at once after collecting them in a list
    if tool_outputs:
        try:
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("Tool outputs submitted successfully.")
            print("-----------------------")
        except Exception as e:
            print("Failed to submit tool outputs:", e)
            print("-----------------------")
    else:
        print("No tool outputs to submit.")

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(messages)
        print("-----------------------")
        if messages.data:
            message_text = messages.data[0].content[0].text.value
            print(message_text)
    else:
        print(run.status)
        return message_text

def run_assistant_fcalling(thread, assistant):

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    print(run.id)
    # Wait for completion
    while run.status not in ["requires_action", "completed"]:
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(run.status)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(new_message)
    if run.status == "completed":
        return new_message, run.status

    elif run.status == "requires_action":
        return run, run.status
    else:
        return "error"

# Uso de la función create_assistant
assistant = assign_assistant()
if assistant is not None and assistant["description"]=="file_search":
    user = input("Enter your name: ").lower()
    question = input("Enter your question: ")
    response = create_response(user, question, assistant)
    print(response)
elif assistant is not None and assistant["description"]=="funtion_calling":
    user = input("Enter your name: ").lower()
    question = input("Enter your question: ")
    response = create_response_fcalling(user, question, assistant)
    print(response)
else:
    print("No assistant selected. follow the next steps to create one: ")
    assistant_type = input("Enter: fs to fuction_file_search or fc to funtion_calling: ")
    name = input("Enter assistant name: ").lower()
    instructions = input("Enter your instructions: ")
    if assistant_type=="fs":
        file = 'PyWhatKit_DB.txt'
        new_assistant = create_assistant.create_assistant_file_search(file, name, instructions)
        print(f"Creating an assistant {new_assistant["name"]} ({new_assistant["description"]}) with id {new_assistant["id"]}")
        user = input("Enter your name: ").lower()
        question = input("Enter your question: ")
        response = create_response(user, question, new_assistant)
        print(response)
    elif assistant_type=="fc":
        new_assistant = create_assistant.create_assistant_funtion_calling(name, instructions, tools=manage_tools.tools)
        print(f"Creating an assistant {new_assistant["name"]} ({new_assistant["description"]}) with id {new_assistant["id"]}")
        user = input("Enter your name: ").lower()
        question = input("Enter your question: ")
        response = create_response_fcalling(user, question, new_assistant)
        print(response)