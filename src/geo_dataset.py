import GEOparse
from fetch_scientifc_names import fetch_scientific_names
from typing import List


class GEODataset:
    def __init__(self, geo_dataset: GEOparse.GEOTypes.GSE):
        metadata = geo_dataset.metadata
        self.title: str = metadata.get("title")[0]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = fetch_scientific_names(metadata.get("sample_taxid", []))
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])

    def __str__(self):
        return f"{self.title}\n{self.experiment_type}\n{self.summary}\n{','.join(self.organisms)}\n{self.overall_design}"
