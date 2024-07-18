from openai import OpenAI
import os
import time
import json
from dotenv import load_dotenv
import datetime
import pywhatkit as kit

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
 
def enviar_mensaje_whatsapp(numero_telefono, mensaje):
    hora_actual = datetime.datetime.now().hour
    minuto_actual = datetime.datetime.now().minute + 1
    if minuto_actual == 60:
        hora_actual += 1
        minuto_actual = 0
    kit.sendwhatmsg(numero_telefono, mensaje, hora_actual, minuto_actual, 15, True, 10)
    #print(f"mensaje enviado a {numero_telefono}")
    return json.dumps({"telefono": numero_telefono, "mensaje": mensaje})

def run_conversation():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "enviar_mensaje_whatsapp",
                "description": "envía un mensaje por whatsapp al número telefónico indicado",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numero_telefono": {
                            "type": "string",
                            "description": "El número de teléfono, por ejemplo, +51959820632",
                        },
                        "mensaje": {
                            "type": "string",
                            "description": "El mensaje de texto que contiene un mensaje, por ejemplo, que tengas un buen día",
                        },
                    },
                    "required": ["numero_telefono", "mensaje"],
                },
            },
        }
    ]

    assistant = client.beta.assistants.create(
        name="funtion_calling_pruebaReal_wapp",
        instructions="Eres un buen asistente. Usa la información del teléfono y el mensaje de texto para enviarlo por whatsapp.",
        model="gpt-4-1106-preview",
        tools=tools
    )
    print(assistant.id)
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="envía un mensaje de texto que indique el otro número al cual se le está enviando el mensaje a los teléfonos +51959812636 y +51984726163",
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
    if tool_call.function.name == "enviar_mensaje_whatsapp":
        arguments = json.loads(tool_call.function.arguments)
        output1 = arguments['numero_telefono']
        output2 = arguments['mensaje']
        print(arguments, output1, output2)
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": enviar_mensaje_whatsapp(output1, output2)
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

time.sleep(10.5)
if run.status == 'completed':
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    print(messages)
    print("-----------------------")
    if messages.data:
        new_message = messages.data[0].content[0].text.value
        print(new_message)
else:
    print(run.status)