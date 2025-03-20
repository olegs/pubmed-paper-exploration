from typing import List


class GEODataset:
    def __init__(self, metadata: dict[str, List[str]]):
        self.id = metadata.get("geo_accession")[0]
        self.title: str = metadata.get("title")[0]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = metadata["organisms"]
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])

    def __str__(self):
        return f"{self.title}\n{self.experiment_type}\n{self.summary}\n{','.join(self.organisms)}\n{self.overall_design}"

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.title == other.title
            and self.experiment_type == other.experiment_type
            and self.summary == other.summary
            and set(self.organisms) == set(other.organisms)
            and self.overall_design == other.overall_design
            and set(self.pubmed_ids) == set(other.pubmed_ids)
        )
