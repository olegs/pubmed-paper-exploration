import requests
from typing import List
from src.ingestion.rate_limit import check_limit
import re


def fetch_geo_accessions(ids: List[str], session: requests.Session) -> List[str]:
    """
    Fetches GEO accessions for the given GEO IDs.

    :param geo_ids: GEO dataset IDs for which to fetch accessions.
    :param sesssion: requests session through which to download the data.
    :return: List of GEO acessions in the same order.
    """
    check_limit()
    geo_summaries = str(
        session.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "gds", "id": ",".join(map(str, ids))},
        ).content
    )

    # Series are the only type of GEO entry that contain all of the infromation
    # we are looking for. Therefore we need to search for series accessions,
    # which begin with GSE.
    return re.findall("Accession: (GSE\\d+)", geo_summaries)
