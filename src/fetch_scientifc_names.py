import requests
from typing import List
import xml.etree.ElementTree as ET
from lru_cache_with_list_support import lru_cache_with_list_support

@lru_cache_with_list_support(maxsize=1000)
def fetch_scientific_names(taxon_ids: List[str]) -> List[str]:
    """
    Fetches scientific names of taxa from the NCBI taxonomy database.
    
    :param taxon_ids: List of NCBI taxonomy IDs.
    :returns: List of corresponding scientific names, in the same order.
    """
    
    efetch_response = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "taxonomy",
            "id": ",".join(map(str, taxon_ids)),
        },
    )
    
    taxa_tree = ET.fromstring(efetch_response.content)
    scientific_name_elements = taxa_tree.findall("./Taxon/ScientificName")
    return [element.text for element in scientific_name_elements]

if __name__ == "__main__":
    print(fetch_scientific_names(["9606", "562", "12721", "10090"]))
    
    print(fetch_scientific_names(["9606", "562"]))
    
    print(fetch_scientific_names(["9606", "562", "9031"]))
    
    print("Current cache:", fetch_scientific_names.get_cache())
