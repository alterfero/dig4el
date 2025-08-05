import openai
import os
api_key = os.getenv("OPEN_AI_KEY")

# https://platform.openai.com/docs/assistants/tools/file-search

def file_search_request(vector_store_names, prompt):
    client = openai.OpenAI(api_key=api_key)
    # get vector store
    vs_list = client.vector_stores.list()
    active_vs = [vs for vs in vs_list if vs.name in vector_store_names]
    if active_vs == []:
        print("No vector store with any of these name")
        print(vs_list)
        return None
    else:
        response = client.responses.create(
            model="gpt-4.1",
            input=prompt,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store.id for vector_store in active_vs]
            }],
            include=["file_search_call.results"]
        )
        return response
