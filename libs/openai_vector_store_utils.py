import os
import openai
import requests
from io import BytesIO
import asyncio
import aiofiles
import time
from typing import Optional

api_key = os.getenv("OPEN_AI_KEY")

async def list_files(includes: str | None = None, limit: int = 1000):
    client = openai.AsyncOpenAI(api_key=api_key)
    after = None
    out = []

    while True:
        resp = await client.files.list(limit=limit, after=after)
        page = resp.data or []
        if includes is not None:
            page = [f for f in page if includes in (f.filename or "")]
        out.extend(page)

        if len(resp.data) < limit:
            break
        after = resp.data[-1].id  # cursor for next page

    return out


async def create_file(path, filename):
    client = openai.AsyncOpenAI(api_key=api_key)
    async with aiofiles.open(os.path.join(path, filename), "rb") as file_content:
        file_bytes = await file_content.read()
        result = await client.files.create(
            file=(filename, file_bytes),
            purpose="assistants"
        )
    print(f"Uploaded file {filename}, id: {result.id}")
    return result.id


async def delete_all_files():
    client = openai.AsyncOpenAI(api_key=api_key)
    files_response = await client.files.list()
    files = files_response.data
    for file in files:
        await client.files.delete(file.id)


async def delete_files_containing(fn_part):
    client = openai.AsyncOpenAI(api_key=api_key)
    files_response = await client.files.list()
    files = files_response.data
    for file in files:
        if fn_part in file.filename:
            await client.files.delete(file.id)


async def create_vector_store(name):
    client = openai.AsyncOpenAI(api_key=api_key)
    vector_store = await client.vector_stores.create(name=name)
    print(f"async create_vector_store: Created vector_store {vector_store.id}")
    return vector_store.id


async def delete_vector_store(vid):
    client = openai.AsyncOpenAI(api_key=api_key)
    await client.vector_stores.delete(vid)


async def list_vector_stores():
    client = openai.AsyncOpenAI(api_key=api_key)
    all_vss = []
    after = None

    while True:
        page = await client.vector_stores.list(limit=100, after=after)
        all_vss.extend(page.data)

        # stop if no more pages or something odd happens
        if not getattr(page, "has_more", False) or not page.data:
            break

        # advance the cursor
        after = getattr(page, "last_id", None) or page.data[-1].id

    return all_vss

# async def list_files_in_vector_store(
#     vector_store_id: str,
#     status: Optional[str] = None,
#     limit: int = 100,
#     max_pages: int = 1000,   # safety
# ):
#     after = None
#     out = []
#     last_after = object()
#
#     for _ in range(max_pages):
#         resp = await client.vector_stores.files.list(
#             vector_store_id=vector_store_id,
#             limit=limit,
#             after=after,
#             filter=status,  # in_progress / completed / failed / cancelled
#         )
#
#         data = resp.data or []
#         out.extend(data)
#
#         # Stop condition per API: has_more + last_id :contentReference[oaicite:1]{index=1}
#         if not getattr(resp, "has_more", False):
#             break
#
#         next_after = getattr(resp, "last_id", None) or (data[-1].id if data else None)
#         if not next_after:
#             break
#
#         # Infinite-loop / non-advancing cursor guard (prevents “hang forever”)
#         if next_after == after or next_after == last_after:
#             raise RuntimeError(f"Pagination cursor not advancing (after={after}, next={next_after})")
#
#         last_after = after
#         after = next_after
#
#     else:
#         raise RuntimeError(f"Hit max_pages={max_pages}; vector store likely huge or pagination stuck.")
#
#     return out

async def list_files_in_vector_store(vector_store_id: str, status: str | None = None, limit: int = 100):
    client = openai.AsyncOpenAI(api_key=api_key)

    after = None
    out = []
    seen_cursors = set()

    while True:
        t0 = time.time()
        print(f"[VS] requesting page after={after} filter={status} limit={limit}")

        try:
            # HARD timeout so “hangs” become an error you can see
            resp = await asyncio.wait_for(
                client.vector_stores.files.list(
                    vector_store_id=vector_store_id,
                    limit=limit,
                    after=after,
                    filter=status,
                ),
                timeout=15,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timed out calling vector_stores.files.list(after={after})")

        dt = time.time() - t0
        data = resp.data or []
        print(f"[VS] got {len(data)} in {dt:.2f}s has_more={getattr(resp,'has_more',None)} last_id={getattr(resp,'last_id',None)}")

        out.extend(data)

        if not getattr(resp, "has_more", False):
            break

        next_after = getattr(resp, "last_id", None)
        if not next_after:
            break

        # Cursor-advance guard (prevents infinite loops)
        if next_after in seen_cursors:
            raise RuntimeError(f"Pagination cursor repeating: {next_after}")
        seen_cursors.add(next_after)

        after = next_after

    return out

async def add_files_to_vector_store(vsid, file_ids):
    client = openai.AsyncOpenAI(api_key=api_key)
    batch = await client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vsid,
        file_ids=file_ids
    )
    return True

async def get_vector_store_id_from_name(vs_name):
    client = openai.AsyncOpenAI(api_key=api_key)
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
    client = openai.AsyncOpenAI(api_key=api_key)
    print("check_vector_store_status")
    # get vector store
    vs_list_response = await client.vector_stores.list()
    active_vs = [vs for vs in vs_list_response.data if vs.id == vsid]
    if active_vs == []:
        print("No vector store id {}".format(vsid))
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

async def delete_empty_vector_stores():
    client = openai.AsyncOpenAI(api_key=api_key)
    vss = await list_vector_stores()
    to_delete = [vs for vs in vss if vs.file_counts.total == 0]
    print("Deleting {} vector store among {}".format(len(to_delete), len(vss)))
    for vs in to_delete:
        print("deleting {}".format(vs.id))
        await delete_vector_store(vs.id)
    print("New VS list: ")
    vss_post = await list_vector_stores()
    print("{} vector stores remaining".format(len(vss_post)))
    print([vs.id for vs in vss_post])
    return vss_post


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


def check_vector_store_status_sync(vsid):
    return asyncio.run(check_vector_store_status(vsid))


def delete_empty_vector_stores_sync():
    return asyncio.run(delete_empty_vector_stores())


# ================================= TEST SCRIPTS ====================================

# delete_vector_store_sync('vs_689a3af047d88191b21b7f18a5ee1020')
#
# def print_vs_list():
#     print("OA Vector Stores list")
#     vss = list_vector_stores_sync()
#     for vs in vss:
#         print(vs)
# print_vs_list()

#print(list_files_in_vector_store_sync("vs_6891146bea508191b24bd91bfadf5c7b"))
#print(list_files_sync())
#delete_files_containing_sync("hypothese")
#delete_empty_vector_stores_sync()

# add_files_to_vector_store_sync("vs_689a3a91a7c48191ab56e68301d892a2", ["file-Y86RUhvJq3qVvsfizLG4m6"])

# delete_empty_vector_stores_sync()

# fs = list_files_in_vector_store_sync("vs_696d47d88e5c8191b447435380815720")
# for f in fs:
#     print(f)