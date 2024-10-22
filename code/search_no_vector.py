import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from urllib.parse import quote, unquote

load_dotenv()

# Set up token provider for Azure AD-based token authentication
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

# Set API version and endpoint for Azure OpenAI
api_version = "2024-07-01-preview"
open_ai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]  # e.g., "https://my-resource.openai.azure.com"

# Initialize AzureOpenAI client
client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=open_ai_endpoint,
    azure_ad_token_provider=token_provider
)

def search_index(query_text: str):
    # Set up SearchClient to query the index
    index_name = os.environ["AZURE_SEARCH_INDEX"]  # Using standard search index
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    credential = AzureKeyCredential(key)
    search_client = SearchClient(service_endpoint, index_name, credential)

    # Perform the keyword search
    search_results = search_client.search(search_text=query_text, top=5)

    # Collect search results into a list
    search_output = []
    for result in search_results:
        search_output.append(f"Document ID: {result['id']}\nContent: {result['content']}\nScore: {result['@search.score']}")
    
    return search_output

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

def encode_text_for_ai_search(text):
    return quote(text, safe="")

# Decode text to return it to its original format for user display
def decode_text_from_ai_search(encoded_text):
    return unquote(encoded_text)
 
if __name__ == "__main__": 
    query_text = 'Can you find information about 6406/5-2 S'

    query_text = encode_text_for_ai_search(query_text)

    print(query_text)

    search_results = search_index(query_text) 

    if search_results: 
        response = generate_chat_completion(query_text, search_results)  # Pass the query_text as well
        print("\n" + "="*40 + "\n") 
        print(f"AI Answer: {response}") 
    else: 
        print("No search results found to answer the query.") 
