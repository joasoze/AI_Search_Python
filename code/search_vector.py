import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI


load_dotenv()

# Set up token provider for Azure AD-based token authentication
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

# Set API version and endpoint for Azure OpenAI
api_version = "2024-07-01-preview"
open_ai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT_BASE"]  # e.g., "https://my-resource.openai.azure.com"

# Initialize AzureOpenAI client
client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=open_ai_endpoint,
    azure_ad_token_provider=token_provider
)

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

    # Collect search results into a list
    search_output = []
    for result in search_results:
        search_output.append(f"Document ID: {result['id']}\nContent: {result['content']}\nScore: {result['@search.score']}")
    
    return search_output

def get_embeddings(text: str):
    # Fetch embeddings using Azure OpenAI and token-based authentication
    embedding_response = client.embeddings.create(
        input=[text],
        model=os.environ["AZURE_OPENAI_EMBEDDING_MODEL_NAME"],  # Azure's embedding deployment
    )
    return embedding_response.data[0].embedding

def generate_chat_completion(query_text, search_results):
    # Start with the original user query
    messages = [{"role": "user", "content": f"Question: {query_text}"}]
    
    # Append search results to the conversation
    for result in search_results:
        messages.append({"role": "user", "content": f"Here are the search results: {result}"})

    # Create chat completion request
    completion = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_MODEL"],
        messages=messages,  # Pass the properly structured messages here
        max_tokens=500,
        temperature=0.7  # Adjust based on desired creativity
    )

    # Use model methods to get the response content instead of subscripting
    response_content = completion.choices[0].message.content

    # Return the response content
    return response_content


if __name__ == "__main__": 
    query_text = "Can you find anything about 25/11-G-3 AY3"


    print(query_text)
    search_results = search_index(query_text) 

    if search_results: 
        response = generate_chat_completion(query_text, search_results)  # Pass the query_text as well
        print("\n" + "="*40 + "\n") 
        print(f"AI Answer: {response}") 
    else: 
        print("No search results found to answer the query.") 

