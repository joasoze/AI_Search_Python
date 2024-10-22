
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()


def get_embeddings(text: str):
    # There are a few ways to get embeddings. This is just one example.
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI

    token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )

    open_ai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    open_ai_key = os.environ["AZURE_OPENAI_KEY"]

    client = AzureOpenAI(
        azure_endpoint=open_ai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=os.environ["AZURE_OPENAI_API_VERSION"]
    )
    embedding = client.embeddings.create(input=[text], model="text-embedding-ada-002")
    return embedding.data[0].embedding
    

def get_index(name: str):
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

    fields = []
    simple_field = SimpleField(name="id", type=SearchFieldDataType.String, key=False, facetable=True, filterable=True)
    fields.append(simple_field)
    key_field = SimpleField(name="keyfield", type=SearchFieldDataType.String, key=True)
    fields.append(key_field)
    simple_field = SearchableField(name="content", type=SearchFieldDataType.String, key=False)
    fields.append(simple_field)
    simple_field = SimpleField(name="category", type=SearchFieldDataType.String, key=False, facetable=True, filterable=True)
    fields.append(simple_field)
    simple_field = SimpleField(name="sourcepage", type=SearchFieldDataType.String, key=False, facetable=True, filterable=True)
    fields.append(simple_field)
    simple_field = SimpleField(name="sourcefile", type=SearchFieldDataType.String, key=False, facetable=True, filterable=True)
    fields.append(simple_field)
    simple_field = SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),searchable=True, vector_search_dimensions=1536, vector_search_profile_name="my-vector-config")
    fields.append(simple_field)


    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="my-vector-config", algorithm_configuration_name="my-algorithms-config")],
        algorithms=[HnswAlgorithmConfiguration(name="my-algorithms-config")],
    )
    return SearchIndex(name=name, fields=fields, vector_search=vector_search)

if __name__ == "__main__":
    index_name = os.environ["AZURE_SEARCH_INDEX_VECTOR"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    credential = AzureKeyCredential(key)
    index_client = SearchIndexClient(service_endpoint, credential)
    index = get_index(index_name)
    index_client.create_index(index)

