from io import StringIO
from typing import Dict, List

import json
import pandas as pd

from src.ingestion.download_geo_datasets import download_geo_datasets
from src.model.geo_dataset import GEODataset


def download_related_paper_datasets(paper_export: Dict[str, object]) -> List[GEODataset]:
    """
    Downloads the GEO datasets of related papers.

    :param paper_export: A dictionary containing the JSON export of a paper
    from PubTrends.
    :returns: A list of GEODatasets containing the datasets of the paper and
    all related papers.
    """
    df = pd.read_json(StringIO(paper_export["df"]))
    df["id"].to_csv("t-cell-exhaustion-ids.csv")
    return download_geo_datasets(df["id"].to_list())


if __name__ == "__main__":
    import json

    paper_export = json.load(open("GEO_Datasets/pubmed-hallmarks-of-aging-an-expanding-universe.json"))
    datasets = download_related_paper_datasets(paper_export)
    print(len(datasets))
