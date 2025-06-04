import asyncio
import concurrent
from typing import List

import aiohttp

from src.ingestion.download_geo_datasets import (download_geo_dataset,
                                                 is_running_in_jupyter)
from src.model.geo_dataset import GEODataset
from src.model.geo_sample import GEOSample


async def download_samples(geo_series: GEODataset, session: aiohttp.ClientSession) -> List[GEODataset]:
    """
    Downloads the samples which are associated with the given series.
    :param geo_series: A GEODataset object that represents the series for
    which the samples need to be downloaded.
    :return: List of GEOSample objects asscociated with that series.
    """
    return await asyncio.gather(
        *(download_geo_dataset(accession, session) for accession in geo_series.sample_accessions)
    )


async def download_samples_with_new_session(geo_series: GEODataset) -> List[GEODataset]:
    async with aiohttp.ClientSession() as session:
        return await download_samples(geo_series, session)


if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_datasets
    datasets = download_geo_datasets(
        [30530648]
    )
    samples = download_samples_sync(datasets[0])

    print(len(samples))
