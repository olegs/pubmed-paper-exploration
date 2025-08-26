from typing import List
from os import path
import os
import asyncio
import concurrent.futures
import GEOparse
import aiohttp
from src.model.geo_dataset import GEODataset
from src.model.geo_sample import GEOSample
from src.ingestion.fetch_geo_ids import fetch_geo_ids
from src.ingestion.fetch_geo_accessions import fetch_geo_accessions, fetch_geo_accessions_europepmc
from src.config import config
from src.exception.http_error import HttpError
import aiofiles

download_folder = config.download_folder


def is_running_in_jupyter():
    """
    Checks if code is being run inside a Jupyter notebook.

    :returns: True if code is being run inside a Jupyter notebook, otherwise
    False.
    """
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


def download_geo_datasets(pubmed_ids: List[int]) -> List[GEODataset]:
    """
    Downloads the GEO datasets for papers with the given PubMed IDs.

    :param dataset_ids: PubMed IDs for which to download GEO datasets.
    :returns: A list containing the dowloaded datasets.
    """

    if not is_running_in_jupyter():
        return asyncio.run(_download_geo_datasets(pubmed_ids))
    else:
        pool = concurrent.futures.ThreadPoolExecutor()
        return pool.submit(asyncio.run, _download_geo_datasets(pubmed_ids)).result()


async def _download_geo_datasets(pubmed_ids: List[int]) -> List[GEODataset]:
    """
    Downloads the GEO datasets for papers with the given PubMed IDs.

    :param dataset_ids: PubMed IDs for which to download GEO datasets.
    :returns: A list containing the dowloaded datasets.
    """
    async with aiohttp.ClientSession() as session:
        geo_ids = await fetch_geo_ids(pubmed_ids, session)
        accessions_geo = fetch_geo_accessions(geo_ids, session)
        accessions_pmc = fetch_geo_accessions_europepmc(pubmed_ids, session)

        accessions = set(await accessions_geo) | set(await accessions_pmc)

        return await asyncio.gather(
            *(download_geo_dataset(accession, session) for accession in accessions)
        )


def _make_directory_if_not_exist(dir_path: str):
    if not path.isdir(dir_path):
        os.mkdir(dir_path)


async def _download_from_url(url: str, destination_path: str, session: aiohttp.ClientSession):
    async with session.get(url) as response:
        if response.status != 200:
            print("Download error, HTTP status:", response.status)
            print("Body:", await response.text())
            raise HttpError(f"Status: {response.status}")
        async with aiofiles.open(destination_path, "wb") as f:
            async for chunk in response.content.iter_chunked(10):
                await f.write(chunk)


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
        try:
            await _download_from_url(dataset_metadata_url, download_path, session)
        except Exception:
            print("Retrying download", accession)
            await _download_from_url(dataset_metadata_url, download_path, session)

    async with aiofiles.open(download_path) as soft_file:
        lines = await soft_file.readlines()
        metadata = GEOparse.GEOparse.parse_metadata(lines)
        return GEODataset(metadata) if accession.startswith("GSE") else GEOSample(metadata)


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
