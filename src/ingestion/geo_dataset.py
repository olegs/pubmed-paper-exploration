import GEOparse
from src.ingestion.fetch_scientifc_names import fetch_scientific_names
from typing import List


class GEODataset:
    def __init__(self, metadata: dict[str, List[str]]):
        self.title: str = metadata.get("title")[0]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = fetch_scientific_names(
            metadata.get("sample_taxid", [])
        )
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])

    def __str__(self):
        return f"{self.title}\n{self.experiment_type}\n{self.summary}\n{','.join(self.organisms)}\n{self.overall_design}"

    def __eq__(self, other):
        return (
            self.title == other.title
            and self.experiment_type == other.experiment_type
            and self.summary == other.summary
            and set(self.organisms) == set(other.organisms)
            and self.overall_design == other.overall_design
            and set(self.pubmed_ids) == set(other.pubmed_ids)
        )
