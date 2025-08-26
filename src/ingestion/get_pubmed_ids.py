from io import StringIO
import asyncio
from typing import List
import time
from src.exception.http_error import HttpError
from src.config import logger
import pandas as pd
import aiohttp
import xml.etree.ElementTree as ET

PUBTRENDS_BASE_URL = "https://pubtrends.info"
EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBTRENDS_POLL_INTERVAL_SECONDS = 1

async def get_pubmed_ids_esearch(query: str) -> List[int]:
    """
    Gets the PubMed IDs of papers related to a search query.
    Uses Esearch to get the PubMed IDs.
    :param query: Search query.
    :return: List of PubMed IDs.
    """
    job_id = None
    async with aiohttp.ClientSession(base_url=EUTILS_BASE_URL) as session:
        async with session.get("esearch.fcgi", params={
            "db": "pubmed",
            "term": query,
            "retmax": 1000,
            "sort": "relevance"
        }) as response:
            if response.status != 200:
                raise HttpError("Esearch error")
            esearch_response = await response.text()
            esearch_xml = ET.fromstring(esearch_response)
            return [int(e.text) for e in esearch_xml.findall(".//Id")]




async def get_pubmed_ids(query: str) -> List[int]:
    """
    Gets the PubMed IDs of papers related to a search query.
    Uses PubTrends to get the PubMed IDs.
    :param query: Search query.
    :return: List of PubMed IDs.
    """
    job_id = None
    async with aiohttp.ClientSession(base_url=PUBTRENDS_BASE_URL) as session:
        async with session.post("/semantic_search_api", data={"query": query}) as response:
            if response.status != 200:
                raise HttpError("PubTrends Semantic Search Error")
            job_info = await response.json()
            if not job_info["success"]:
                raise HttpError(
                    "Invalid semantic search response from PubTrends")
            job_id = job_info["jobid"]
        logger.info(f"Submitted PubTrends job: {job_id}")
        await wait_for_job_to_complete(session, job_id)
        async with session.get("/get_result_api",
                               params={
                                   "jobid": job_id,
                                   "query": query
                               }):
            if response.status != 200:
                return HttpError("PubTrends get job result error")
            pubtrends_result = await response.json()
            df = await asyncio.to_thread(pd.read_json, StringIO(pubtrends_result["df"]))
            return df["id"].to_csv()


async def wait_for_job_to_complete(pubtrends_session: aiohttp.ClientSession, job_id: str):
    for _ in range(1800):
        async with pubtrends_session.get(f"/check_status_api/{job_id}") as response:
            if response.status != 200:
                raise HttpError("PubTrends Check Status Error")
            job_status_response = await response.json()
            job_status = job_status_response["status"]
            if job_status.lower() not in ["success", "unknown", "pending"]:
                raise HttpError("PubTrends job failed")
            elif job_status == "success":
                return
        time.sleep(PUBTRENDS_POLL_INTERVAL_SECONDS)
    raise HttpError("PubTrends job timeout")


if __name__ == "__main__":
    query = input("Pubtrends search query: ")
    pubmed_ids = asyncio.run(get_pubmed_ids_esearch(query))
    print(f"Found {len(pubmed_ids)} for {query}")
