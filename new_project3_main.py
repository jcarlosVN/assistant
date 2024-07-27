from openai import OpenAI
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
file = 'reclamos.xlsx'



def load_protuct_list(file):
    df = pd.read_excel(file)
    df['response_strings'] = df.apply(lambda x: f'''root: {x['root']}
                                      product: {x['product']}''', axis=1)
    df.to_csv('new_reclamos.csv', index=False)
    return df

df = load_protuct_list(file)
#print(df)

system_promt = "you are an assistant that, given a claim, comes up with a claim root and claim product."

all_conversation = []
for idx, row in df.iterrows():
    all_conversation.append({"messages": [{"role": "system", "content": system_promt}, 
                                          {"role": "user", "content": row['prompt']}, 
                                          {"role": "assistant", "content": row['response_strings']}]})

with open('instances.jsonl', 'w') as f:
    for conversation in all_conversation:
        json.dump(conversation, f)
        f.write('\n')

#response = client.files.create(
#    file=open("instances.jsonl", "rb"),
#    purpose="fine-tune"
#)
#print(response)
fiel_id = 'file-N98Ml0JJboPyUcbpxOwunpge'

response = client.fine_tuning.jobs.create(
  training_file=fiel_id, 
  model="gpt-3.5-turbo"
)
print(response)
job_id = "ftjob-ZxdBHmL728ut0wmAsHCZv9cb"

while response.status != "succeeded":
    # Be nice to the API
    time.sleep(0.5)
    job = client.fine_tuning.jobs.retrieve(response.id)
    print(job.status)