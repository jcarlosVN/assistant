from openai import OpenAI
import os
import time
import json
from dotenv import load_dotenv
import datetime
import requests
from bs4 import BeautifulSoup

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
 
def scraping():
    url = 'https://dermotiendashopping.com/marcas.html'
    lista_productos=[]
    fecha = datetime.datetime.now()

    for i in range (1, 999):
        url_p = f'{url}?p={i}'
        #print(url_p)
        page = requests.get(url_p)
        soup = BeautifulSoup(page.content, 'html.parser')
        grilla_products = soup.find('div', class_='products wrapper grid products-grid')
        if grilla_products is None:
            print('break')
            #url_final = f'{url}?p={i-1}'
            #print(url_final)
            break
        else:
            print('lleno')
            print(url_p)
            products = grilla_products.find_all('div', class_='product-item-info')
            for product in products:
                img = product.find('img', class_='product-image-photo')
                name = product.find('a', class_='product-item-link')
                price = product.find('span', class_='price')
                link = product.find('a', class_='product photo product-item-photo')
                #print('------------------', img['src'], name.get_text(strip=True), price.get_text(strip=True), '------------------')
                lista={}
                lista['producto']= name.get_text(strip=True)
                lista['precio_txt']= price.get_text(strip=True)
                lista['img']= img['src']
                lista['link']= link.get('href')
                lista_productos.append(lista)
    return lista_productos


def buscar_producto(nombre_producto):
    lista_productos = scraping()
    for producto in lista_productos:
        if producto["producto"].lower() == nombre_producto.lower():
            return json.dumps({"prod": producto["producto"], "prec": producto["precio_txt"], "link": producto["link"]})
    return json.dumps({"error": "Producto no encontrado"})

def run_conversation():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "buscar_producto",
                "description": "busca el nombre del producto en la lista de productos dermatológicos cargados",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre_producto": {
                            "type": "string",
                            "description": "El nombre del producto, por ejemplo, Bioderma Photoderm AKN Mat SPF30 40ml",
                        },
                    },
                    "required": ["nombre_producto"],
                },
            },
        }
    ]

    assistant = client.beta.assistants.create(
        name="funtion_calling_pruebaReal_dermotienda",
        instructions="Eres amigable. Usa la información del nombre del producto para indicar el link del producto.",
        model="gpt-4-1106-preview",
        tools=tools
    )
    print(assistant.id)
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="busca el producto Sesderma Dryses desodorante Hombre 75ml",
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
    if tool_call.function.name == "buscar_producto":
        arguments = json.loads(tool_call.function.arguments)
        output1 = arguments['nombre_producto']
        print(arguments, output1)
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": buscar_producto(output1)
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