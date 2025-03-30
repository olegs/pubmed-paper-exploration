from typing import List
import requests
from src.ingestion.rate_limit import check_limit
from src.exception.entrez_error import EntrezError

elink_request_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"


def fetch_geo_ids(pubmed_ids: List[int], session: requests.Session) -> List[int]:
    """
    Fetches GEO dataset ids for papers with the specified PubMed IDs.

    :param pubmed_ids: List of PubMed IDs to fetch GEO dataset ids for.
    :param sesssion: requests session through which to download the data.
    :returns: A list that contains the IDs of the GEO datasets associated with the PubMed IDs.
    """
    check_limit() 
    response = session.get(
        elink_request_url,
        params={
            "dbfrom": "pubmed",
            "db": "gds",
            "linkname": "pubmed_gds",
            "id": ",".join(map(str, pubmed_ids)),
            "retmode": "json",
        },
    ).json()
    if "ERROR" in response:
        raise EntrezError("Error when fetching GEO IDs")

    geo_ids_str = response["linksets"][0]["linksetdbs"][0]["links"]
    return [int(geo_id) for geo_id in geo_ids_str]


if __name__ == "__main__":
    geo_ids = fetch_geo_ids(
        [30530648, 31820734, 31018141, 38539015, 33763704, 32572264]
    )
    print(f"Found {len(geo_ids)} GEO datasets")
    for id in geo_ids:
        print(id)
