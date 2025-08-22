from typing import List, Dict
from src.model.geo_sample import GEOSample
from dateutil.parser import parse as parse_date
import json

platform_map = None
with open("src/model/gpl_platform_map.json") as f:
    platform_map = json.load(f)

GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR = " ; "

class GEODataset:
    def __init__(self, metadata: dict[str, List[str]]):
        self.id = metadata.get("geo_accession")[0]
        self.title: str = metadata.get("title")[0]
        self.experiment_types: List[str] = metadata["type"]
        self.experiment_type: str = metadata["type"][0]
        self.summary: str = metadata.get("summary", [""])[0]
        self.organisms: List[str] = metadata.get("sample_organism", [])
        self.overall_design: str = metadata.get("overall_design", [""])[0]
        self.pubmed_ids: List[str] = metadata.get("pubmed_id", [])
        self.platform_ids: str = metadata.get("platform_id", [])
        self.sample_accessions: List[str] = metadata.get("sample_id", [])
        self.samples: List[GEOSample] | None = None
        self.publication_date = parse_date(
            metadata["submission_date"][0]) if "submission_date" in metadata else None
        self.platforms: List[str] = [platform_map.get(
            gpl, gpl) for gpl in self.platform_ids]
        self.contact_name: str = metadata.get("contact_name", [",,"])[0]
        self.contact_name = " ".join(self.contact_name.split(","))
        self.contact_email: str = metadata.get("contact_email", [""])[0]
        self.sample_count: int = len(self.sample_accessions)
        self.supplementary_files: List[str] = metadata.get(
            "supplementary_file", [])
        # Make the links downloadable
        self.supplementary_files = list(map(lambda link: link.replace(
            "ftp://", "https://"), self.supplementary_files))
        self.supplementary_filenames = list(
            map(lambda link: link.split("/")[-1], self.supplementary_files))
        self.metadata = metadata

    def get_unique_values(self, characteristic: str):
        if not self.samples:
            return []
        else:
            return list(set(
                sample.characteristics[characteristic] for sample in self.samples if characteristic in sample.characteristics
            ))

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
    
    def get_str_with_sample_characteristics(self):
        string = f"Title: {self.title}{GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR}Experiment type: {self.experiment_type}{GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR}Overall design: {self.overall_design}{GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR}"
        string += self._get_sample_characteristics_str(GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR)
        bern2_character_limit = 3000
        return self._shorten_string_to_limit(string, GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR, bern2_character_limit)

    def _get_sample_characteristics_str(self, sep="\n"):
        string = ""
        characteristics = {}
        for sample in self.samples:
            for key, value in sample.characteristics.items():
                if key in characteristics:
                    characteristics[key].add(value)
                else:
                    characteristics[key] = set([value])
        
        for key, values in characteristics.items():
            if len(values) < 20:
                string += f"{key}: {','.join(values)}" + sep
        return string

    def _shorten_string_to_limit(self, string, sep, limit):
        while len(string) > limit:
            lines = string.split(sep)
            lines.remove(max(lines, key=len))
            string = sep.join(lines)
        
        return string
    
    def get_metadata_str(self, sep="\n"):
        string = f"{self.experiment_type}{sep}{self.summary}{sep}{self.overall_design}{sep}"
        string += self._get_sample_characteristics_str(sep)
        bern2_character_limit = 3000
        return self._shorten_string_to_limit(string, sep, bern2_character_limit)



    def to_dict(self) -> Dict:
        """
        Dumps the dataset into a JSON-serializible dict.
        """
        return {
            "id": self.id,
            "title": self.title,
            "experiment_type": self.experiment_type,
            "experiment_types": self.experiment_types,
            "summary": self.summary,
            "organisms": self.organisms,
            "overall_design": self.overall_design,
            "pubmed_ids": self.pubmed_ids,
            "platforms": self.platforms,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "sample_count": self.sample_count,
            "supplementary_files": self.supplementary_files,
            "supplementary_filenames": self.supplementary_filenames,
        }
