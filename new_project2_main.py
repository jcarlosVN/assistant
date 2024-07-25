from openai import OpenAI
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
file = 'PyWhatKit_DB.txt'
file2 = 'product_list.xlsx'

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
    print(vector_store.id)
    return vector_store.id

def load_protuct_list(file2):
    df = pd.read_excel(file2)
    product_list = df['product'].tolist()
    return product_list

product_list=load_protuct_list(file2)

#v_s = vector_store(file)
#assistant = client.beta.assistants.create(
#    name="new_sub_proyect",
#    instructions="Como assitente, se te dará un producto e identificarás su precio. Es imperativo que tu respuesta solo indique el precio, no menciones nada más",
#    model="gpt-4o",
#    tools=[{"type": "file_search"}],
#    tool_resources={"file_search": {"vector_store_ids": [v_s]}}
#)
#print(assistant.id)
#thread = client.beta.threads.create()
#print(thread.id)
#>>>>>> vs_L6kwYe5eQ5oTj5X3MLu91FTI
#>>>>>> asst_sclcnHy9ohCkzWRjVGHdG1II
#>>>>>> thread_0BsQDxWbyYAkYqjNLx3A4Sf3

def run_assistant(thread, assistant):

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    # Wait for completion
    while run.status not in ["failed", "completed"]:
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(run.status)
    
    if run.status=="failed":
        return run.status
    else:
        # Retrieve the Messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        new_message = messages.data[0].content[0].text.value
        return new_message

def get_current_price(product_list):
    assistant = client.beta.assistants.retrieve('asst_sclcnHy9ohCkzWRjVGHdG1II')
    thread = client.beta.threads.retrieve('thread_0BsQDxWbyYAkYqjNLx3A4Sf3')

    prices = {}
    for product in product_list:
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"cuál es el precio para el producto {product}"
        )

        output = run_assistant(thread, assistant)
        prices[product] = output

    # Convert the prices dictionary to a DataFrame
    df = pd.DataFrame(list(prices.items()), columns=['Product', 'Price'])

    # Save the DataFrame to an Excel file
    df.to_excel('product_prices.xlsx', index=False)

    return json.dumps(prices)

a = get_current_price(product_list)
print(a)