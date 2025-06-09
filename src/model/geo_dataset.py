from typing import List, Dict
from src.model.geo_sample import GEOSample
from dateutil.parser import parse as parse_date


class GEODataset:
    def __init__(self, metadata: dict[str, List[str]]):
        self.id = metadata.get("geo_accession")[0]
        self.title: str = metadata.get("title")[0]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = metadata.get("sample_organism", [])
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])
        self.platform_ids: str = metadata.get("platform_id", [])
        self.sample_accessions: List[str] = metadata.get("sample_id", [])
        self.samples: List[GEOSample] | None = None
        self.publication_date = parse_date(metadata["submission_date"][0]) if "submission_date" in metadata else None
        self.metadata = metadata

    def __str__(self):
        if self.is_not_superseries():
            return f"{self.title}\n{self.experiment_type}\n{self.summary}\n{','.join(self.organisms)}\n{self.overall_design}"
        else:
            # The summary and overall design fields for SuperSeries do not contain any useful information.
            # (Their content always is "This SuperSeries is composed of the SubSeries listed below." and "Refer to individual Series")
            # When this content is not removed, all SuperSeries get grouped into cluster despite being about vastly different topics.
            return f"{self.title}\n{self.experiment_type}\n{','.join(self.organisms)}"

    def __eq__(self, other):
        return (
            self.title == other.title
            and self.experiment_type == other.experiment_type
            and self.summary == other.summary
            and set(self.organisms) == set(other.organisms)
            and self.overall_design == other.overall_design
            and set(self.pubmed_ids) == set(other.pubmed_ids)
        )

    def is_not_superseries(self):
        return (
            self.summary
            != "This SuperSeries is composed of the SubSeries listed below."
        )

    def to_dict(self) -> Dict:
        """
        Dumps the dataset into a JSON-serializible dict.
        """
        return {
            "id": self.id,
            "title": self.title,
            "experiment_type": self.experiment_type,
            "summary": self.summary,
            "organisms": self.organisms,
            "overall_design": self.overall_design,
            "pubmed_ids": self.pubmed_ids,
        }
