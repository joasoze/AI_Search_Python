import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from urllib.parse import quote, unquote

load_dotenv()

# Set API version and endpoint for Azure OpenAI
api_version = "2024-07-01-preview"
open_ai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]  # e.g., "https://my-resource.openai.azure.com"
openai_api_key = os.environ["AZURE_OPENAI_KEY"]  # Azure OpenAI API Key

# Initialize AzureOpenAI client using the API key
client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=open_ai_endpoint,
    api_key=openai_api_key
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
    query_text = 'Can you find wellbores where DEEPSEA STAVANGER was the drilling facility'
    query_text = encode_text_for_ai_search(query_text)

    search_results = search_index(query_text)
    # Loop through search results and decode each one
    search_results = [decode_text_from_ai_search(result) for result in search_results]


    if search_results: 
        response = generate_chat_completion(query_text, search_results)  # Pass the query_text as well
        print("\n" + "="*40 + "\n") 
        print(f"AI Answer: {response}") 
    else: 
        print("No search results found to answer the query.")
