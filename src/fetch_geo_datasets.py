from typing import List
import requests

elink_request_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"


def fetch_geo_ids(pubmed_ids: List[int]) -> List[int]:
    response = requests.get(
        elink_request_url,
        params={
            "dbfrom": "pubmed",
            "db": "gds",
            "linkname": "pubmed_gds",
            "id": ",".join(map(str, pubmed_ids)),
            "retmode": "json",
        },
    ).json()
    geo_ids_str = response["linksets"][0]["linksetdbs"][0]["links"]
    return [int(geo_id) for geo_id in geo_ids_str]


if __name__ == "__main__":
    geo_ids = fetch_geo_ids(
        [30530648, 31820734, 31018141, 38539015, 33763704, 32572264]
    )
    print(f"Found {len(geo_ids)} GEO datasets")
    for id in geo_ids:
        print(id)
