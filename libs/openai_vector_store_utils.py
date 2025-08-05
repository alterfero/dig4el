import os
import openai
import requests
from io import BytesIO
import asyncio
import aiofiles

api_key = os.getenv("OPEN_AI_KEY")
client = openai.AsyncOpenAI(api_key=api_key)


async def list_files(includes=None):
    files_response = await client.files.list()
    files = files_response.data
    if includes is not None:
        filtered_files = [f for f in files if includes in f.filename]
    else:
        filtered_files = files
    return filtered_files


async def create_file(path, filename):
    async with aiofiles.open(os.path.join(path, filename), "rb") as file_content:
        file_bytes = await file_content.read()
        result = await client.files.create(
            file=(filename, file_bytes),
            purpose="assistants"
        )
    print(f"Uploaded file {filename}, id: {result.id}")
    return result.id


async def delete_all_files():
    files_response = await client.files.list()
    files = files_response.data
    for file in files:
        await client.files.delete(file.id)


async def delete_files_containing(fn_part):
    files_response = await client.files.list()
    files = files_response.data
    for file in files:
        if fn_part in file.filename:
            await client.files.delete(file.id)


async def create_vector_store(name):
    vector_store = await client.vector_stores.create(name=name)
    print(f"Created vector_store {vector_store.id}")
    return vector_store.id


async def delete_vector_store(vid):
    await client.vector_stores.delete(vid)


async def list_vector_stores():
    vss = await client.vector_stores.list()
    return vss.data

async def list_files_in_vector_store(vid):
    vector_stores_response = await client.vector_stores.files.list(vector_store_id=vid)
    return vector_stores_response.data


async def add_files_to_vector_store(vsid, file_ids):
    batch = await client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vsid,
        file_ids=file_ids
    )
    return True

async def get_vector_store_id_from_name(vs_name):
    vs_list = await client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name == vs_name]
    if active_vs == []:
        print("No vector store with that name")
        print(vs_list)
        return None
    else:
        vector_store = active_vs[0]
        return vector_store.id


async def check_vector_store_status(vsid):
    print("check_vector_store_status")
    # get vector store
    vs_list_response = await client.vector_stores.list()
    active_vs = [vs for vs in vs_list_response.data if vs.id == vsid]
    if active_vs == []:
        print("No vector store with that id")
        print(vs_list_response)
        return None
    else:
        print("found vector store {}".format(vsid))
        vector_store = active_vs[0]
        print("id: {}".format(vector_store.id))
        result = await client.vector_stores.files.list(
            vector_store_id=vector_store.id
        )
    print(result)
    try:
        return result.data[0].status
    except:
        return "No status found"


# ================================= SYNC CALLS =====================================

def list_files_sync(includes=None):
    return asyncio.run(list_files(includes=includes))


def create_file_sync(path, filename):
    return asyncio.run(create_file(path, filename))


def delete_files_containing_sync(fn_part):
    return asyncio.run(delete_files_containing(fn_part))


def list_vector_stores_sync():
    return asyncio.run(list_vector_stores())


def list_files_in_vector_store_sync(vid):
    return asyncio.run(list_files_in_vector_store(vid))


def create_vector_store_sync(name):
    return asyncio.run(create_vector_store(name))


def delete_vector_store_sync(vid):
    return asyncio.run(delete_vector_store(vid))


def add_files_to_vector_store_sync(vsid, file_ids):
    return asyncio.run(add_files_to_vector_store(vsid, file_ids))


def check_vector_store_status_sync(vs_name):
    return asyncio.run(check_vector_store_status(vs_name))


# ================================= TEST SCRIPTS ====================================

#delete_vector_store_sync('vs_6891146bea508191b24bd91bfadf5c7b')

# def print_vs_list():
#     vss = list_vector_stores_sync()
#     for vs in vss:
#         print(vs)
# print_vs_list()

#print(list_files_in_vector_store_sync("vs_6891146bea508191b24bd91bfadf5c7b"))
#print(list_files_sync())
#delete_files_containing_sync("hypothese")