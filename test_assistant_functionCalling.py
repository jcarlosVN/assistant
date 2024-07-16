from openai import OpenAI
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
 
def get_current_temperature(location):
    """Get the current temperature in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "100"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "200"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "300"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def run_conversation():
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

    assistant = client.beta.assistants.create(
        name="funtion_calling_pruebaReal_01",
        instructions="You are a weather bot. Use the provided functions to answer questions.",
        model="gpt-4-1106-preview",
        tools=tools
    )
    print(assistant.id)
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="What's the weather like in Tokyo and Bogota?",
    )
    print(thread.id)
    new_message, messages, run = run_assistant(thread, assistant)
    print(new_message)
    print("-----------------------")
    print(messages)
    print("-----------------------")
    print(run)
    print("-----------------------")
    return new_message, messages, run, thread, assistant

def run_assistant(thread, assistant):

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    print(run.id)
    # Wait for completion
    while run.status != "requires_action":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(run.status)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    return new_message, messages, run

new_message, messages, run, thread, assistant = run_conversation()

tool_outputs = []

# Loop through each tool in the required action section
for tool_call in run.required_action.submit_tool_outputs.tool_calls:
    if tool_call.function.name == "get_current_temperature":
        arguments = json.loads(tool_call.function.arguments)
        location = arguments['location']
        print(arguments, location)
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": get_current_temperature(location)
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