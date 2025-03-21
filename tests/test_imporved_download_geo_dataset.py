import pytest
import GEOparse
from typing import List
from src.ingestion.download_geo_datasets import download_geo_dataset
from src.ingestion.fetch_scientifc_names import fetch_scientific_names


class SlowGEODataset:
    def __init__(self, geo_dataset: GEOparse.GEOTypes.GSE):
        metadata = geo_dataset.metadata
        self.title: str = metadata.get("title")[0]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = fetch_scientific_names(
            metadata.get("sample_taxid", [])
        )
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])


def slow_download_geo_dataset(accession: str) -> SlowGEODataset:
    """
    Donwloads the GEO dataset with the given accession.

    :param accession: GEO accession for the series (ex. GSE12345)
    :return: GEO
    """
    dataset = GEOparse.get_GEO(geo=accession, destdir="./Downloads")
    return SlowGEODataset(dataset)


@pytest.mark.parametrize("accession", [("GSE127893"), ("GSE216999")])
def test_imporved_download_geo_dataset(accession):
    assert download_geo_dataset(accession) == slow_download_geo_dataset(accession)
