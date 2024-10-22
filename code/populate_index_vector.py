import os
from dotenv import load_dotenv
from typing import Dict
import openai 
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
import tiktoken
import json
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI


from azure.search.documents.indexes.models import (
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        SimpleField,
        SearchableField,
        VectorSearch,
        VectorSearchProfile,
        HnswAlgorithmConfiguration,
    )
load_dotenv()



token_provider = get_bearer_token_provider(
DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
#AI Search stuff
endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
index_name = os.environ["AZURE_SEARCH_INDEX_VECTOR"]

## Create a service client
search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

#OpenAI stuff
open_ai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT_BASE"]
open_ai_key = os.environ["AZURE_OPENAI_KEY"]

client = AzureOpenAI(
    azure_endpoint=open_ai_endpoint,
    azure_ad_token_provider=token_provider,
    api_version=os.environ["AZURE_OPENAI_API"]
) 

# Define the tokenizer for the model
tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")

def count_tokens(text):
    """Helper function to count tokens in a text string."""
    return len(tokenizer.encode(text))

def split_json(data, max_tokens):
    """Efficiently split the JSON into chunks by processing each key-value pair."""
    chunks = []
    current_chunk = {}
    token_count = 0

    # Parse the JSON string into a Python object
    json_data = json.loads(data)

    # Traverse through the key-value pairs in the JSON
    for key, value in json_data.items():
        # Prepare to add the key-value pair to the current chunk
        potential_chunk = {key: value}
        # Convert this chunk to a string and count the tokens
        potential_chunk_str = json.dumps(potential_chunk)
        potential_chunk_tokens = count_tokens(potential_chunk_str)

        # If adding this key-value pair exceeds the token limit, finalize the current chunk
        if token_count + potential_chunk_tokens >= max_tokens:
            chunks.append(json.dumps(current_chunk))  # Add the current chunk to the list
            current_chunk = {}  # Reset for the new chunk
            token_count = 0  # Reset token count for the new chunk

        # Add the key-value pair to the current chunk
        current_chunk[key] = value
        token_count += potential_chunk_tokens

    # Add the final chunk if there is any remaining data
    if current_chunk:
        chunks.append(json.dumps(current_chunk))

    return chunks



def extract_id_and_content(blob_content):
    data = json.loads(blob_content)
    id = data.get("id")
    content = json.dumps(data).replace('"', "'")
    return id, content

def extract_id(blob_content):
    data = json.loads(blob_content)
    id = data.get("id")
    return id

def encode_id(id_value):
    return id_value.replace(":", "_")

def generate_embeddings(text):
    embedding = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002" # This must match the custom deployment name you chose for your model.
        )
    return embedding.data[0].embedding
# Example usage



# Convert the JSON string to a Python object
from azure.storage.blob import BlobServiceClient
#if needed, run: pip install azure-storage-blob

# Use DefaultAzureCredential for user-based authentication
credential = DefaultAzureCredential()

# Define the storage account and container names
account_url = f"https://{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}.blob.core.windows.net"
container_name = os.environ["AZURE_STORAGE_NAME_DATA"]

# Create a BlobServiceClient object using the DefaultAzureCredential
blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)


# Get a reference to the container
container_client = blob_service_client.get_container_client(container_name)

# List all blobs (documents) in the container
blob_list = container_client.list_blobs()
counter = 0
max_tokens = 7000  # Set a limit slightly below the model's max token count

# Iterate over the blobs and read their contents
for blob in blob_list:
    counter = counter + 1
    if counter > 10:  # Limit to 10 documents for testing
        break
    # Get the blob client for the current blob
    blob_client = container_client.get_blob_client(blob.name)
     # Download the blob's content
    blob_content = blob_client.download_blob().readall().decode("utf-8")
    blob_name = blob_client.blob_name
    id, content = extract_id_and_content(blob_content)

    output_fields = []
    # Split JSON based on token limits
    result_split = split_json(json.dumps(json.loads(blob_content)), max_tokens)

    for i, chunk in enumerate(result_split):  
        key = encode_id(id)+"-"+str(i)   
        print(len(chunk))
        document = {
            "id": str(id),
            "content": id+" - "+ chunk,
            "keyfield": key,
            "sourcefile": blob_name,
            "category": "",
            "sourcepage": blob_name + " - "+ str(i),
            "contentVector": generate_embeddings(id+ "-"+ chunk)
        }
        output_fields.append(document)
        result = search_client.upload_documents(documents=output_fields)
        counter += 1
        #print("Upload of new document succeeded: {}".format(result[0].succeeded)+ ' counter = '+ str(counter))
        #print(f"Chunk {i+1}: {chunk}\n")
        if counter % 100 == 0:
            print(f"{counter} documents processed.")

        

    
  

