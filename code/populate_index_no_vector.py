import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
import json
from urllib.parse import quote
import math

# Load environment variables from .env file
load_dotenv()

# Use DefaultAzureCredential for user-based authentication
credential = DefaultAzureCredential()

# Set up Azure Cognitive Search credentials using DefaultAzureCredential
search_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
search_index_name = os.environ["AZURE_SEARCH_INDEX"]

# Create a SearchClient object using Azure AD authentication
search_client = SearchClient(endpoint=search_endpoint, index_name=search_index_name, credential=credential)

# Define the storage account and container names
account_url = f"https://{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}.blob.core.windows.net"
container_name = os.environ["AZURE_STORAGE_NAME_DATA"]

# Create a BlobServiceClient object using the DefaultAzureCredential
blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

# Get a reference to the container
container_client = blob_service_client.get_container_client(container_name)

def replace_nan(obj):
    if isinstance(obj, dict):
        return {k: replace_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan(i) for i in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return ''  # Replace NaN with an empty string or other placeholder
    else:
        return obj

# Encode text to make it safe for AI Search ingestion
def encode_text_for_ai_search(text):
    return quote(text, safe="")

def extract_id_and_content(blob_content, filename):
    # Convert the JSON content into a string
    json_string = blob_content.decode("utf-8") if isinstance(blob_content, bytes) else blob_content
    
    try:
        # Parse the string to a JSON object
        data = json.loads(json_string)
        
        # Recursively replace NaN values
        data = replace_nan(data)
        
        # Extract id and content
        id = data.get("id", "No ID")
        content = json.dumps(data).replace('"', "'")  # Replace double quotes with single quotes for content
        content = encode_text_for_ai_search(content)
        
        return id, content  # Ensure both id and content are returned
    except Exception as e:
        print(f"Error parsing or processing content: {e}")
        return None, None  # Return None in case of an error

# Function to encode the ID (optional, if your IDs contain special characters)
def encode_id(id_value):
    return id_value.replace(":", "_")

counter = 0
# List all blobs (documents) in the container
blob_list = container_client.list_blobs()

# Iterate over the blobs and read their contents, stopping after 10 documents
for blob in blob_list:

    counter += 1

    # Get the blob client for the current blob
    blob_client = container_client.get_blob_client(blob.name)
    # Download the blob's content and ensure proper UTF-8 decoding
    blob_content = blob_client.download_blob().readall().decode("utf-8")

    blob_name = blob_client.blob_name
    
    # Extract the ID and content from the blob
    id, content = extract_id_and_content(blob_content, blob_name)
    
    if id and content:
        # Create a document to upload to Azure Cognitive Search
        document = {
            "id": str(id),
            "content": id + " - " + content,
            "keyfield": encode_id(id),
            "category": "",
            "sourcepage": blob_name            
        }
        
        # Upload the document to Azure Cognitive Search
        result = search_client.upload_documents(documents=[document])
    
    if counter % 100 == 0:
        print(f"{counter} documents processed.")
