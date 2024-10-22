import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

def get_embeddings(text: str):
    # Fetch embeddings from Azure OpenAI
    import openai
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )

    open_ai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT_BASE"]
    open_ai_key = os.environ["AZURE_OPENAI_KEY"]

    client = AzureOpenAI(
        azure_endpoint=open_ai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=os.environ["AZURE_OPENAI_API"]
    )
    embedding = client.embeddings.create(input=[text], model="text-embedding-ada-002")
    return embedding.data[0].embedding

def search_index(query_text: str):
    # Get embeddings for the query
    query_embedding = get_embeddings(query_text)
    
    # Set up SearchClient to query the index
    index_name = os.environ["AZURE_SEARCH_INDEX_VECTOR"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    credential = AzureKeyCredential(key)
    search_client = SearchClient(service_endpoint, index_name, credential)

    # Prepare the vectorized query
    vector_query = VectorizedQuery(
        vector=query_embedding,
        fields="contentVector"  # Search based on the "contentVector" field
    )

    # Perform the search
    search_results = search_client.search(search_text=None, vector_queries=[vector_query], top=5)

    # Display the results
    print(f"Search results for: '{query_text}'")
    for result in search_results:
        print(f"Document ID: {result['id']}")
        print(f"Content: {result['content']}")
        print(f"Score: {result['@search.score']}")
        print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    # Example query text
    query_text = "Can you find anything about the Production licence 255B"
    
    # Perform the search using vector embeddings
    search_index(query_text)
