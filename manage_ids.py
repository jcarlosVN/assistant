import json

# Función para cargar los datos del archivo txt
def load_data():
    try:
        with open("assistants_threads_users_db.txt", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Función para guardar los datos en el archivo txt
def save_data(data):
    with open("assistants_threads_users_db.txt", "w") as file:
        json.dump(data, file)