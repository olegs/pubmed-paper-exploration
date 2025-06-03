from typing import Dict, List
from src.ingestion.download_geo_datasets import download_geo_datasets
from src.model.geo_dataset import GEODataset
import pandas as pd

def download_related_paper_datasets(paper_export: Dict[str, object]) -> List[GEODataset]:
    """
    Downloads the GEO datasets of related papers.

    :param paper_export: A dictionary containing the JSON export of a paper
    from PubTrends.
    :returns: A list of GEODatasets containing the datasets of the paper and
    all related papers.
    """
    df = pd.read_json(paper_export["df"])
    return download_geo_datasets(df["id"].to_list())


if __name__ == "__main__":
    import json
    paper_export = json.load(open("GEO_Datasets/pubmed-hallmarks-of-aging-an-expanding-universe.json"))
    datasets = download_related_paper_datasets(paper_export)
    print(len(datasets))

    #df = pd.read_json(paper_export["df"])
    #df = df[["id","title","abstract","year","type","keywords","mesh","doi","aux","authors","journal","total","x","y","comp","2023"]]
    #pd.set_option('display.max_columns', None)
    #print(df.head())
    #for column in df.columns:
    #    print(column)



