from typing import List
import asyncio
import aiohttp
from src.ingestion.rate_limit import check_limit
from src.exception.entrez_error import EntrezError

elink_request_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"


async def fetch_geo_ids(
    pubmed_ids: List[int], session: aiohttp.ClientSession
) -> List[int]:
    """
    Fetches GEO dataset ids for papers with the specified PubMed IDs.

    :param pubmed_ids: List of PubMed IDs to fetch GEO dataset ids for.
    :param sesssion: aiohtttp session through which to download the data.
    :returns: A list that contains the IDs of the GEO datasets associated with the PubMed IDs.
    """
    check_limit()
    async with session.post(
        elink_request_url,
        params={
            "dbfrom": "pubmed",
            "db": "gds",
            "linkname": "pubmed_gds",
            "retmode": "json",
        },
        data={
            "id": ",".join(map(str, pubmed_ids)),
        }
    ) as response:
        assert response.status == 200
        response = await response.json()
        if "ERROR" in response:
            raise EntrezError("Error when fetching GEO IDs")

        try:
            geo_ids_str = response["linksets"][0]["linksetdbs"][0]["links"]
            return [int(geo_id) for geo_id in geo_ids_str]
        except KeyError:
            return []


async def main():
    async with aiohttp.ClientSession() as session:
        geo_ids = await fetch_geo_ids(
            [30530648, 31820734, 31018141, 38539015, 33763704, 32572264], session
        )
        print(f"Found {len(geo_ids)} GEO datasets")
        for id in geo_ids:
            print(id)


if __name__ == "__main__":
    asyncio.run(main())
