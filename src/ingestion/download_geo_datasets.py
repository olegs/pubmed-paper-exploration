import GEOparse
from typing import List
import requests
from os import path
from src.model.geo_dataset import GEODataset
from src.ingestion.fetch_geo_ids import fetch_geo_ids
from src.ingestion.rate_limit import check_limit
from src.ingestion.fetch_geo_accessions import fetch_geo_accessions
from src.ingestion.fetch_scientifc_names import fetch_scientific_names
from GEOparse.utils import smart_open, download_from_url


def download_geo_datasets(pubmed_ids: List[int]) -> List[GEODataset]:
    """
    Downloads the GEO datasets for papers with the given PubMed IDs.

    :param dataset_ids: PubMed IDs for which to download GEO datasets.
    :returns: A list containing the dowloaded datasets.
    """
    # Title, Experiment type, Summary, Organism, Overall design
    geo_ids = fetch_geo_ids(pubmed_ids)
    accessions = fetch_geo_accessions(geo_ids)
    return [download_geo_dataset(accession) for accession in accessions]


def download_geo_dataset(accession: str) -> GEODataset:
    """
    Donwloads the GEO dataset with the given accession.

    :param accession: GEO accession for the dataset (ex. GSE12345)
    :return: GEO dataset
    """
    dataset_metadata_url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=quick"
    download_path = f"./Downloads/{accession}.txt"
    if not path.isfile(download_path):
        check_limit()
        download_from_url(dataset_metadata_url, download_path)

    with open(download_path) as soft_file:
        metadata = GEOparse.GEOparse.parse_metadata(soft_file)
        metadata["organisms"] = fetch_scientific_names(metadata.get("sample_taxid", []))
        return GEODataset(metadata)


if __name__ == "__main__":
    datasets = download_geo_datasets(
        [30530648, 31820734, 31018141, 38539015, 33763704, 32572264]
    )
    print(f"Downloaded {len(datasets)} datasets")

    for dataset in datasets:
        print("-" * 10)
        print(dataset)
        print(f"ID: {dataset.id}")
        print("-" * 10)
