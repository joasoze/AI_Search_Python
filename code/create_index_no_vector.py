
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient


load_dotenv()

def get_index(name: str):
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        SimpleField,
        SearchableField,
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
    return SearchIndex(name=name, fields=fields)

if __name__ == "__main__":
    index_name = os.environ["AZURE_SEARCH_INDEX"]
    key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    credential = AzureKeyCredential(key)
    index_client = SearchIndexClient(service_endpoint, credential)
    index = get_index(index_name)
    index_client.create_index(index)

