
import os
import openai
import requests
from io import BytesIO

api_key = os.getenv("OPEN_AI_KEY")

def create_vector_store(name):
    client = openai.OpenAI(api_key=api_key)
    vector_store = client.vector_stores.create(name=name)
    print(vector_store)

def list_vector_stores():
    client = openai.OpenAI(api_key=api_key)
    vector_store = client.vector_stores.list()
    print(vector_store)

def create_file(file_path):
    client = openai.OpenAI(api_key=api_key)
    if file_path.startswith("http://") or file_path.startswith("https://"):
        # Download the file content from the URL
        response = requests.get(file_path)
        file_content = BytesIO(response.content)
        file_name = file_path.split("/")[-1]
        file_tuple = (file_name, file_content)
        result = client.files.create(
            file=file_tuple,
            purpose="assistants"
        )
    else:
        # Handle local file path
        with open(file_path, "rb") as file_content:
            result = client.files.create(
                file=file_content,
                purpose="assistants"
            )
    print(result.id)
    return result.id

def add_file_to_vector_store(vector_store_name, file_name):
    client = openai.OpenAI(api_key=api_key)
    # get vector store
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name == vector_store_name]
    if active_vs == []:
        print("No vector store with that name")
        print(vs_list)
        return None
    else:
        vector_store = active_vs[0]
        available_files = client.files.list()
        target_file = [f for f in available_files if f.filename == file_name]
        if target_file == []:
            print("No file on openai available with that name")
            print(available_files)
            return None
        else:
            file = target_file[0]
            file_id = file.id
            client.vector_stores.files.create(
                vector_store_id=vector_store.id,
                file_id=file_id
            )
            return client.vector_stores.files.list(
                vector_store_id=vector_store.id
            )


def list_files():
    client = openai.OpenAI(api_key=api_key)
    files = client.files.list()
    print(files)

def get_vector_store_id_from_name(vs_name):
    client = openai.OpenAI(api_key=api_key)
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name == vector_store_name]
    if active_vs == []:
        print("No vector store with that name")
        print(vs_list)
        return None
    else:
        vector_store = active_vs[0]
        return vector_store.id

def add_all_files_from_folder_to_oa(folder_path):
    client = openai.OpenAI(api_key=api_key)
    uploaded_filenames = []
    print(os.listdir(folder_path))
    usable_filenames = [f for f in os.listdir(folder_path) if f[-4:] in [".pdf", ".docx"]]
    existing_filenames = [f.filename for f in client.files.list()]
    print("{} files will be used".format(len(usable_filenames)))
    for file_name in usable_filenames:
        if file_name in existing_filenames:
            print("{} already uploaded".format(file_name))
        else:
            file_path = folder_path + file_name
            with open(file_path, "rb") as file_content:
                result = client.files.create(
                    file=file_content,
                    purpose="assistants"
                )
            print("{} processed, id={}".format(file_name, result.id))
            uploaded_filenames.append(file_name)
    print("All files added")
    return uploaded_filenames


def delete_all_files():
    client = openai.OpenAI(api_key=api_key)
    files = client.files.list()
    for file in files:
        client.files.delete(file.id)


def add_all_files_from_folder_to_vector_store(vs_name, folder_path, create_vs_if_needed=True):
    client = openai.OpenAI(api_key=api_key)
    # get vector store
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name == vs_name]
    if active_vs == []:
        if create_vs_if_needed:
            vector_store = client.vector_stores.create(name=vs_name)
        else:
            print("No vector store with that name")
            print(vs_list)
            return None
    else:
        vector_store = active_vs[0]
        # add all files from local folder to oa
        print("Adding all compatible files from {}".format(folder_path))
        uploaded_filenames = add_all_files_from_folder_to_oa(folder_path)
        print("Adding all these files to the {} vector store".format(vector_store.name))
        available_filenames = [f.filename for f in client.files.list() if f.filename in uploaded_filenames]
        print("{} files to add".format(len(available_filenames)))
        for file_name in available_filenames:
            print("adding {}".format(file_name))
            add_file_to_vector_store(vs_name, file_name)
        print("All files added, check status for processing")

def check_vector_store_status(vs_name):
    client = openai.OpenAI(api_key=api_key)
    # get vector store
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name == vs_name]
    if active_vs == []:
        print("No vector store with that name")
        print(vs_list)
        return None
    else:
        vector_store = active_vs[0]
        result = client.vector_stores.files.list(
            vector_store_id=vector_store.id
        )
    print(result)

local_file_path = "/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/"
file_name = "3_Krausse_Francois_final.pdf"


# create_file(local_file_path+file_name)
#list_files()
#add_file_to_vector_store("Mwotlap", "3_Krausse_Francois_final.pdf")
#add_all_files_from_folder_to_vector_store("Mwotlap", local_file_path)
check_vector_store_status("Mwotlap")


## DOCUMENTATION
# https://platform.openai.com/docs/api-reference/vector-stores
# https://platform.openai.com/docs/guides/tools-file-search