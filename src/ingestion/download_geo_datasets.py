import GEOparse
from typing import List
from geo_dataset import GEODataset
import requests
import re
from fetch_geo_ids import fetch_geo_ids
from rate_limit import check_limit
from soft_metadata_line_iterator import metadata_line_iterator
from fetch_geo_accessions import fetch_geo_accessions
from GEOparse.utils import smart_open


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

    :param accession: GEO accession for the dataset (ex. GSE12345)
    :return: GEO
    """
    print("Downloading {}", accession)
    download_path, _ = GEOparse.get_GEO_file(geo=accession, destdir="./Downloads")
    with smart_open(download_path) as soft_file:
        metadata_lines = metadata_line_iterator(soft_file)
        metadata = GEOparse.GEOparse.parse_metadata(metadata_lines)
        return GEODataset(metadata)

    return GEODataset(dataset)


if __name__ == "__main__":
    datasets = download_geo_datasets(
        [30530648, 31820734, 31018141, 38539015, 33763704, 32572264]
    )
    print(f"Downloaded {len(datasets)} datasets")

    for dataset in datasets:
        print("-" * 10)
        print(dataset)
        print("-" * 10)
