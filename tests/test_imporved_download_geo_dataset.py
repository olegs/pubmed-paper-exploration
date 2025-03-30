import pytest
import GEOparse
import requests
import aiohttp
import xml.etree.ElementTree as ET
from typing import List
from src.ingestion.download_geo_datasets import download_geo_dataset


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


class SlowGEODataset:
    def __init__(self, geo_dataset: GEOparse.GEOTypes.GSE):
        metadata = geo_dataset.metadata
        self.title: str = metadata.get("title")[0]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = fetch_scientific_names(
            metadata.get("sample_taxid", [])
        )
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])


def slow_download_geo_dataset(accession: str) -> SlowGEODataset:
    """
    Donwloads the GEO dataset with the given accession.

    :param accession: GEO accession for the series (ex. GSE12345)
    :return: GEO
    """
    dataset = GEOparse.get_GEO(geo=accession, destdir="./Downloads")
    return SlowGEODataset(dataset)


@pytest.mark.parametrize("accession", [("GSE127893"), ("GSE216999")])
@pytest.mark.asyncio
async def test_imporved_download_geo_dataset(accession):
    async with aiohttp.ClientSession() as session:
        assert await download_geo_dataset(accession, session) == slow_download_geo_dataset(accession)
