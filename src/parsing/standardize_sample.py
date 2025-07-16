from typing import Dict, List
from src.tissue_and_cell_type_standardization.gliner_recognizer import GlinerRecognizer
from src.tissue_and_cell_type_standardization.get_standard_name_fasttext import FasttextNormalizer
from src.parsing.age.get_age import get_age
from src.parsing.age.extract_age import extract_age
from src.model.geo_sample import GEOSample
from src.tissue_and_cell_type_standardization.ner_nen_pipeline import NER_NEN_Pipeline, PipelineResult

class ParsedField:
    def __init__(self, field_name, value_from_source_name, value_in_characteristics, standard_value_from_source_name, standard_value_from_characteristics):
        self.field_name = field_name
        self.value_from_source_name = value_from_source_name
        self.value_in_characteristics = value_in_characteristics
        self.standard_value_from_source_name = standard_value_from_source_name
        self.standard_value_from_characteristics = standard_value_from_characteristics
    
    def to_dict(self):
        return {
            f"{self.field_name}_value_from_source_name":  self.value_from_source_name,
            f"{self.field_name}_value_in_characteristics":  self.value_in_characteristics,
            f"{self.field_name}_standard_value_from_source_name":  self.standard_value_from_source_name,
            f"{self.field_name}_standard_value_from_characteristics":  self.standard_value_from_characteristics,
        }

class ParsedSample:
    def __init__(self, id, source_name, fields: List[ParsedField]):
        self.id = id
        self.soruce_name = source_name
        self.fields = fields
    
    def to_dict(self):
        sample_dict = {}
        sample_dict["id"] = self.id
        sample_dict["source_name"] = self.soruce_name
        for field in self.fields:
            sample_dict.update(field.to_dict())
        return sample_dict

def _get_age_field(sample: GEOSample, source_name_annotations: List[PipelineResult]) -> ParsedSample:
    annotation_in_source_name = [ann for ann in source_name_annotations if ann.entity_class.lower()=="age"]
    annotation_in_source_name = annotation_in_source_name[0] if len(annotation_in_source_name) > 0 else None
    value_from_source_name = annotation_in_source_name.mention if annotation_in_source_name else None
    value_in_characteristics = sample.characteristics.get("age")
    standard_value_from_source_name = extract_age(value_from_source_name) if value_from_source_name else None
    standard_value_from_characteristics = get_age(sample)
    return ParsedField("age", value_from_source_name, value_in_characteristics, standard_value_from_source_name, standard_value_from_characteristics)

def _get_parsed_field(field_name:str, ner_type: str, sample: GEOSample, source_name_annotations: List[PipelineResult], ner_nen_pipeline: NER_NEN_Pipeline) -> ParsedSample:
    annotation_in_source_name = [ann for ann in source_name_annotations if ann.entity_class.lower()==ner_type.lower()]
    annotation_in_source_name = annotation_in_source_name[0] if len(annotation_in_source_name) > 0 else None
    value_from_source_name = annotation_in_source_name.mention if annotation_in_source_name else None
    value_in_characteristics = sample.characteristics.get(field_name)
    standard_value_from_source_name = annotation_in_source_name.standard_name if annotation_in_source_name is not None else None
    standard_value_from_characteristics = ner_nen_pipeline.normalizer(value_in_characteristics).standard_name if value_in_characteristics is not None else None
    return ParsedField(field_name, value_from_source_name, value_in_characteristics, standard_value_from_source_name, standard_value_from_characteristics)

def parse_sample(sample: GEOSample, ner_nen_pipeline: NER_NEN_Pipeline) -> ParsedSample:
    fields = []
    source_name = sample.metadata.get("source_name_ch1", [""])[0]
    source_name_annotations = ner_nen_pipeline(source_name)

    fields.append(_get_age_field(sample, source_name_annotations))
    fields.append(_get_parsed_field("tissue", "tissue", sample, source_name_annotations, ner_nen_pipeline))
    fields.append(_get_parsed_field("cell type", "cell type", sample, source_name_annotations, ner_nen_pipeline))
    fields.append(_get_parsed_field("disease", "healthy or disease", sample, source_name_annotations, ner_nen_pipeline))

    return ParsedSample(sample.accession, source_name, fields)


if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_dataset
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    from src.tissue_and_cell_type_standardization.get_standard_name_fasttext import FasttextNormalizer
    from src.tissue_and_cell_type_standardization.ner_nen_pipeline import NER_NEN_Pipeline
    import os
    import glob
    import asyncio
    import random
    from aiohttp.client import ClientSession
    import pandas
    recognizer = GlinerRecognizer(["Tissue", "Cell Type", "Age", "Healthy or Disease", "Cell Line", "Gender"])
    print("Recognizer ready")
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    normalizer = FasttextNormalizer("BioWordVec_PubMed_MIMICIII_d200.vec.bin", mesh_lookup)
    print("Normalizer ready")
    ner_nen_pipeline = NER_NEN_Pipeline(recognizer, normalizer)

    file_pattern = "GEO_Datasets/GSM*.txt"
    gsm_files = glob.glob(file_pattern)
    accessions = []
    for filename in gsm_files:
        accession = os.path.basename(filename).strip(".txt")
        accessions.append(accession)

    async def download_accessions(accessions: List[str]):
        async with ClientSession() as session:
            return await asyncio.gather(*(download_geo_dataset(accession, session) for accession in accessions))
    
    samples = asyncio.run(download_accessions(accessions))

    parsed_samples = [parse_sample(sample, ner_nen_pipeline) for sample in samples]
    df = pandas.DataFrame(sample.to_dict() for sample in parsed_samples)
    df = df.sort_values(by="id")
    df.to_csv("parsed_sample_metadata.csv")
    print(df.head())
    

