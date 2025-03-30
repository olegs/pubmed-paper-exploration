from typing import List
from os import path
import os
import asyncio
import GEOparse
import aiohttp
from src.model.geo_dataset import GEODataset
from src.ingestion.fetch_geo_ids import fetch_geo_ids
from src.ingestion.fetch_geo_accessions import fetch_geo_accessions
from src.config import config

download_folder = config.download_folder


def download_geo_datasets(pubmed_ids: List[int]) -> List[GEODataset]:
    """
    Downloads the GEO datasets for papers with the given PubMed IDs.

    :param dataset_ids: PubMed IDs for which to download GEO datasets.
    :returns: A list containing the dowloaded datasets.
    """

    return asyncio.run(_download_geo_datasets(pubmed_ids))


async def _download_geo_datasets(pubmed_ids: List[int]) -> List[GEODataset]:
    """
    Downloads the GEO datasets for papers with the given PubMed IDs.

    :param dataset_ids: PubMed IDs for which to download GEO datasets.
    :returns: A list containing the dowloaded datasets.
    """
    async with aiohttp.ClientSession() as session:
        geo_ids = await fetch_geo_ids(pubmed_ids, session)
        accessions = await fetch_geo_accessions(geo_ids, session)

        return await asyncio.gather(
            *(download_geo_dataset(accession, session) for accession in accessions)
        )


def _make_directory_if_not_exist(dir_path: str):
    if not path.isdir(dir_path):
        os.mkdir(dir_path)


async def _download_from_url(url: str, destination_path: str, session: aiohttp.ClientSession):
    async with session.get(url) as response:
        assert response.status == 200
        with open(destination_path, "w") as f:
            f.write(await response.text())


async def download_geo_dataset(accession: str, session: aiohttp.ClientSession) -> GEODataset:
    """
    Donwloads the GEO dataset with the given accession.

    :param accession: GEO accession for the dataset (ex. GSE12345)
    :param session: aiohttp session.
    :return: GEO dataset
    """
    dataset_metadata_url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&targ=self&form=text&view=quick"
    download_path = path.join(download_folder, f"{accession}.txt")

    _make_directory_if_not_exist(download_folder)
    if not path.isfile(download_path):
        await _download_from_url(dataset_metadata_url, download_path, session)

    with open(download_path) as soft_file:
        relevant_lines = filter(
            lambda line: not line.startswith("!Series_sample_id"), soft_file
        )
        metadata = GEOparse.GEOparse.parse_metadata(relevant_lines)
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
