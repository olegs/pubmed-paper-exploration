from typing import Dict
import requests
import json
from typing import List
from src.ingestion.rate_limit import RateLimited
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup 
from src.tissue_and_cell_type_standardization.named_entity_recognizer import NamedEntityRecognizer, NamedEntity
from src.tissue_and_cell_type_standardization.entity_normalizer import EntityNormalizer, NormalizationResult
from src.tissue_and_cell_type_standardization.ner_nen_pipeline import NER_NEN_Pipeline, PipelineResult


@RateLimited(max_per_second=3)

def get_standard_name_bern2(text, mesh_id_map, mesh_lookup, url="http://bern2.korea.ac.kr/plain") -> str | None:
    response = requests.post(url, json={'text': text})
    while response.status_code != 200:
        response = requests.post(url, json={'text': text})
    cleaned_response = response.text.replace(": NaN", ": -1")
    response = json.loads(cleaned_response)
    candidate_ids = []
    for annotation in sorted(response["annotations"], key=lambda ann: ann["prob"]):
        annotation_ids = list(filter(lambda id: id.startswith("mesh"), annotation["id"]))
        annotation_ids = [ann_id[len("mesh:"):] for ann_id in annotation_ids]
        candidate_ids += annotation_ids
    
    candidate_terms = [mesh_id_map[candidate_id] for candidate_id in candidate_ids if candidate_id in mesh_id_map]
    candidate_terms = list(filter(lambda term: term.strip().lower() in mesh_lookup, candidate_terms))
    return candidate_terms[0] if candidate_terms else None

class BERN2Pipeline(NER_NEN_Pipeline):
    def __init__(self, mesh_id_map: Dict[str, str], ncbi_gene: Dict[str, str], url: str="http://localhost:8888/plain"):
        self.url = url
        self.mesh_id_map = mesh_id_map
        self.ncbi_gene = ncbi_gene

    #@RateLimited(3)
    def __call__(self, text: str) -> List[PipelineResult]:
        response = requests.post(self.url, json={'text': text})
        while response.status_code != 200:
            response = requests.post(self.url, json={'text': text})
        cleaned_response = response.text.replace(": NaN", ": -1")
        response = json.loads(cleaned_response)

        entities = []
        for annotation in response["annotations"]:
            mesh_ids = list(filter(lambda id: id.startswith("mesh"), annotation["id"]))
            if (not mesh_ids) and ("CUI-less" not in annotation["id"]):
                cui = annotation["id"][0]
                ontology = cui.split(":")[0]
                entities.append(PipelineResult(annotation["mention"], annotation["obj"], self.ncbi_gene.get(cui, cui), ontology,  cui, annotation["prob"]))

            for mesh_id in filter(lambda id: id.startswith("mesh"), annotation["id"]):
                mesh_id = mesh_id[len("mesh:"):]
                standard_name = self.mesh_id_map.get(mesh_id)
                if standard_name:
                    entities.append(PipelineResult(annotation["mention"], annotation["obj"], standard_name, "MeSH",  mesh_id, annotation["prob"]))
                else:
                    entities.append(PipelineResult(annotation["mention"], annotation["obj"], None, "MeSH",  None, annotation["prob"]))
        
        return entities


class BERN2Recognizer(NamedEntityRecognizer):
    def __init__(self, url: str="http://bern2.korea.ac.kr/plain"):
        self.url = url

    @RateLimited(3)
    def extract_named_entities(self, text):
        # TODO: Add retry
        response = requests.post(self.url, json={'text': text}).json()
        entities = []
        for annotation in response["annotations"]:
            entities.append(NamedEntity(annotation["mention"], annotation["obj"], annotation["prob"]))
            
        return list(sorted(entities, key=lambda e: e.score))

class BERN2MeshNormalizer(EntityNormalizer):
    def __init__(self, mesh_id_map: Dict[str, str], url: str="http://bern2.korea.ac.kr/plain"):
        self.url = url
        self.mesh_id_map = mesh_id_map

    @RateLimited(3)
    def normalize_entity(self, entity: str):
        response = requests.post(self.url, json={'text': text}).json()
        annotations = response["annotations"]
        if not annotations:
             return None
        for annotation in sorted(annotations, key=lambda ann: ann["prob"]):
            try:
                mesh_id = next(filter(lambda id: id.startswith("mesh"), annotation["id"]))
                mesh_id = mesh_id[len("mesh:"):]
                standard_name = mesh_id_map[mesh_id]
                return NormalizationResult(entity, standard_name, "MeSH", mesh_id, annotation["prob"])
            except StopIteration:
                continue
        
        return None



if __name__ == '__main__':
    import json
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    mesh_id_map = {entry.id: key.strip().lower()
                   for key, entry in mesh_lookup.items()}
    ncbi_gene = {}
    with open("gene_ontology_map.json") as f:
        ncbi_gene = json.load(f) 
    recognizer = BERN2Recognizer()
    normalizer = BERN2MeshNormalizer(mesh_id_map)
    pipeline = BERN2Pipeline(mesh_id_map, ncbi_gene)

    while True:
        text = input(">")
        print("-----")
        for e in pipeline(text):
            print(e)
        print("------")