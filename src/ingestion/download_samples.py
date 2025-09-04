import asyncio
import concurrent
from typing import List

import aiohttp

from src.ingestion.download_geo_datasets import (download_geo_dataset,
                                                 is_running_in_jupyter)
from src.model.geo_dataset import GEODataset


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


def download_samples_for_datasets(geo_series: List[GEODataset]) -> List[GEODataset]:
    """
    Downloads the samples which are associated with the given series.
    The samples for each series will be stored in the samples attribute of
    the datasets.
    :param geo_series: A list of GEODataset objects that represents the series for
    which the samples need to be downloaded.
    :return: List of GEOSample objects asscociated with that series.
    """

    async def _download_samples(datasets: List[GEODataset]):
        # Download samples
        samples = set()  # We are using a set because some samples can occur twice. For example, a sample appears twice when it is in a subseries and superseries
        async with aiohttp.ClientSession() as session:
            for series in datasets:
                try:
                    series.samples = await download_samples(series, session)
                    samples.update(series.samples)
                except aiohttp.ServerDisconnectedError:
                    session = await session.close()
                    session = aiohttp.ClientSession()
                    series.samples = await download_samples(series, session)
                    samples.update(series.samples)

        return list(samples)

    if not is_running_in_jupyter():
        return asyncio.run(_download_samples(geo_series))
    else:
        pool = concurrent.futures.ThreadPoolExecutor()
        return pool.submit(asyncio.run, _download_samples(geo_series)).result()


if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_datasets

    datasets = download_geo_datasets(
        [30530648]
    )
    samples = download_samples_for_datasets(datasets)

    print(len(datasets[0].samples))
