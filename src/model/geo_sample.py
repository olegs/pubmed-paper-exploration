from typing import Dict, List


class GEOSample:
    def __init__(self, metadata: Dict):
        self.metadata = metadata
        self.characteristics = GEOSample._parse_characteristics(
            metadata.get("characteristics_ch1"))
        self.title = metadata.get("title")[0]
        self.accession = metadata.get("geo_accession")[0]
        self.organism = metadata.get("organism_ch1")[0]
        self.description = " ".join(metadata.get("description", []))
        self.data_processing = metadata.get("data_processing", [])
        self.treatment_protocol = " ".join(
            metadata.get("treatment_protocol_ch1", []))
        self.sample_type = metadata.get("type")[0]

    def _parse_characteristics(characteristics: List[str]) -> Dict[str, str]:
        """
        Parses the characterstics key value pairs and stores them in a 
        dictionary.
        :param characteristics: Sample characterestics extracted from the 
        metadata from a sample.
        :return: Dictionary where the keys are the names of the characteristics.
        """
        characteristics_dict = {}
        for characteristic in characteristics:
            key, value = characteristic.split(": ", 1)
            characteristics_dict[key] = value
        return characteristics_dict

    def __eq__(self, other):
        return self.accession == other.accession
    
    def __hash__(self):
        return hash(self.accession + self.title)