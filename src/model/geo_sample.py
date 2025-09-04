from typing import Dict, List


class GEOSample:
    def __init__(self, metadata: Dict):
        self.metadata = metadata
        self.title = metadata.get("title", ["N/A"])[0]
        self.accession = metadata.get("geo_accession", ["N/A"])[0]
        self.organism = metadata.get("organism_ch1", ["N/A"])[0]
        self.description = " ".join(metadata.get("description", []))
        self.data_processing = metadata.get("data_processing", [])
        self.treatment_protocol = " ".join(
            metadata.get("treatment_protocol_ch1", []))
        self.sample_type = metadata.get("type", ["N/A"])[0]
        self.characteristics = self._parse_characteristics(
            metadata.get("characteristics_ch1"))
        self.dataset_id = metadata.get("series_id", ["N/A"])[0]

    def _parse_characteristics(self, characteristics: List[str]) -> Dict[str, str]:
        """
        Parses the characterstics key value pairs and stores them in a 
        dictionary.
        :param characteristics: Sample characterestics extracted from the 
        metadata from a sample.
        :return: Dictionary where the keys are the names of the characteristics.
        """
        if characteristics is None:
            return {}
        characteristics_dict = {}
        for characteristic in characteristics:
            try:
                key, value = characteristic.split(":", 1)
                characteristics_dict[key.lower()] = value.strip().lower()
            except ValueError:
                unparsed_key = "unparsed_characteristics"
                current_unparsed = characteristics_dict.get(unparsed_key, "")
                characteristics_dict[unparsed_key] = current_unparsed + \
                                                     "|" + characteristic
        return characteristics_dict

    def __eq__(self, other):
        return self.accession == other.accession

    def __hash__(self):
        return hash(self.accession + self.title)

    def __str__(self):
        string = f"Accession:{self.accession}\n{self.title}\nsource:{self.metadata.get('source_name_ch1', [''])[0]}\ndescription:{self.description}\n"
        string += "\n".join(f"{characteristic}: {value}" for characteristic, value in self.characteristics.items())
        return string
