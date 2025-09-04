import asyncio
import itertools
import re
from typing import List

import aiohttp
from lxml import etree

from src.ingestion.rate_limit import check_limit


async def fetch_geo_accessions(
        geo_ids: List[str], session: aiohttp.ClientSession
) -> List[str]:
    """
    Fetches GEO accessions for the given GEO IDs from the NCBI E-Utilities.

    :param geo_ids: GEO dataset IDs for which to fetch accessions.
    :param sesssion: aiohttp session through which to download the data.
    :return: List of GEO acessions in the same order.
    """
    check_limit()
    async with session.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "gds", "id": ",".join(map(str, geo_ids))},
    ) as response:
        assert response.status == 200
        geo_summaries = await response.text()

        # Series are the only type of GEO entry that contain all of the infromation
        # we are looking for. Therefore we need to search for series accessions,
        # which begin with GSE.
        return re.findall("Accession: (GSE\\d+)", geo_summaries)


async def fetch_geo_accessions_europepmc(
        pubmed_ids: List[str], session: aiohttp.ClientSession
) -> List[str]:
    """
    Fetches GEO accessions for several PubMed IDs from the EuropePMC database.

    :param pubmed_ids: PubMed IDs of the papers for which to fetch GEO dataset
    accessions.
    :param sesssion: aiohttp session through which to download the data.
    :return: List of GEO acessions associated with the papers.
    """
    # There is no explicit rate limit for EuropePMC
    batch_size = 8
    batches = [pubmed_ids[i:i + batch_size]
               for i in range(0, len(pubmed_ids), batch_size)]
    accession_batches = await asyncio.gather(
        *(_fetch_geo_accession_batch_europepmc(batch, session) for batch in batches)
    )
    accessions = itertools.chain.from_iterable(accession_batches)
    # There may multiple annotations for the same GEO accession
    return list(set(accessions))


async def _fetch_geo_accession_batch_europepmc(
        pubmed_ids: List[str], session: aiohttp.ClientSession
) -> List[str]:
    """
    Fetches GEO references in a list of papers (max 8 papers) from EuropePMC's
    annotations API.

    :param pubmed_ids: PubMed IDs of the papers for which to fetch GEO dataset
    accessions.
    :param sesssion: aiohttp session through which to download the data.
    :return: List of GEO acessions associated with the papers.
    """
    article_ids = ",".join([f"MED:{id}" for id in pubmed_ids])
    async with session.get(
            f"https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds",
            params={
                "articleIds": article_ids,
                "type": "Accession Numbers",
                "subType": "geo",
                "format": "xml"
            },
    ) as pmc_response:
        assert pmc_response.status == 200
        pmc_response = await pmc_response.text()
        root = etree.fromstring(pmc_response)
        accessions = root.xpath("//exact[starts-with(text(),'GSE')]/text()")
        return accessions
