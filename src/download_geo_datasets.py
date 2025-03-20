import GEOparse
from typing import List
import json
from geo_dataset import GEODataset
import requests
import re
from fetch_geo_ids import fetch_geo_ids
from rate_limit import check_limit



def download_geo_datasets(pubmed_ids: List[int]) -> List[GEODataset]:
    """
    Downloads the GEO datasets for papers with the given PubMed IDs.

    :param dataset_ids: PubMed IDs for which to download GEO datasets.
    :returns: A list containing the dowloaded datasets.
    """
    # Title, Experiment type, Summary, Organism, Overall design
    geo_ids = fetch_geo_ids(pubmed_ids)
    accessions = fetch_geo_accessions(geo_ids)
    print(accessions)
    return [download_geo_dataset(accession) for accession in accessions]


def download_geo_dataset(accession: str) -> GEODataset:
    """
    Donwloads the GEO dataset with the given accession.

    :param accession: GEO accession for the series (ex. GSE12345)
    :return: GEO
    """
    print("Downloading {}", accession)
    dataset = GEOparse.get_GEO(geo=accession)
    return GEODataset(dataset)


def fetch_geo_accessions(ids: List[str]) -> List[str]:
    """
    Fetches GEO accessions for the given GEO IDs.

    :param geo_ids: GEO dataset IDs for which to fetch accessions.
    :return: List of GEO acessions in the same order.
    """
    check_limit()
    geo_summaries = str(requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        {"db": "gds", "id": ",".join(map(str, ids))},
    ).content)

    # Series are the only type of GEO entry that contain the infromation
    # we are looking for. Therefore we need to search for series accessions,
    # which begin with GSE.
    return re.findall("Accession: (GSE\d+)", geo_summaries)


if __name__ == "__main__":
    datasets = download_geo_datasets([30530648,31820734,31018141,38539015,33763704,32572264])
    print(f"Downloaded {len(datasets)} datasets")

    for dataset in datasets:
        print("-"*10)
        print(dataset)
        print("-"*10)

