from typing import Dict
from src.standardization.bern2_pipeline import BERN2Pipeline
from typing import Dict
from src.standardization.angel_normalizer import ANGELMeshNormalizer
from src.utils.get_line_at_index import get_line_at_index
from src.model.geo_dataset import GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR
from src.standardization.is_mesh_term_in_anatomy_or_disease import is_term_in_one_of_categories


class BERN2AngelPipeline(BERN2Pipeline):
    def __init__(self, mesh_lookup, ncbi_gene: Dict[str, str], url: str = "http://localhost:8888/plain", must_normalize_to_mesh=False):
        mesh_id_to_term_map = {entry.id: key.strip().lower()
                               for key, entry in mesh_lookup.items()}
        super().__init__(mesh_id_to_term_map, ncbi_gene, url)
        self.angel = ANGELMeshNormalizer(mesh_lookup)
        self.must_normalize_to_mesh = must_normalize_to_mesh
        self.angel_cache = {}
        self.cell_type_candidates = [key for key in mesh_lookup if is_term_in_one_of_categories(
            key, mesh_lookup, ["A", "C04.588", "C04.557"])]
        self.all_candidates = self.angel.candidates

    def preprocess_annotations(self, annotations, text):
        for annotation in annotations:
            if "CUI-less" in annotation["id"] or (self.must_normalize_to_mesh and not any(term_id.startswith("mesh:") for term_id in annotation["id"])):
                self.assign_entity_type_based_on_line(annotation, text)
                mesh_id = self.normalize_to_mesh_id(annotation)
                annotation["id"].append("mesh:" + mesh_id)

        return annotations

    def normalize_to_mesh_id(self, annotation: Dict[str, str]) -> str:
        """
        Normalizes the annotated mention and returns the normalized entity's 
        MeSH ID.
        :param anntotaion: BERN2 Annotation.
        """
        self.set_angel_candidates(annotation)
        mention = annotation["mention"]
        mention = mention.strip().lower()
        entity_type = annotation["obj"]
        cache_key = (mention, entity_type)
        if cache_key in self.angel_cache:
            return self.angel_cache[cache_key].cui

        normalization = self.angel.normalize_entity(mention)
        self.angel_cache[cache_key] = normalization
        return normalization.cui

    def set_angel_candidates(self, annotation: Dict[str, str]):
        """
        Sets the candidates ANGEL considers to match the entity type of the 
        annotation.

        :param annotation: BERN2 annotation.
        """
        entity_type = annotation["obj"]
        if entity_type in ["cell_type", "cell_line"]:
            self.angel.candidates = self.cell_type_candidates
        else:
            self.angel.candidates = self.all_candidates

    def assign_entity_type_based_on_line(self, annotation, text):
        line = get_line_at_index(
            text, annotation["span"]["begin"], GEO_DATASET_CHARCTERISTICS_STR_SEPARATOR)
        if line.startswith("cell type: "):
            annotation["obj"] = "cell_type"
        elif line.startswith("cell line: "):
            annotation["obj"] = "cell_line"


if __name__ == "__main__":
    import json
    from src.standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    mesh_id_map = {entry.id: key.strip().lower()
                   for key, entry in mesh_lookup.items()}
    ncbi_gene = {}
    with open("gene_ontology_map.json") as f:
        ncbi_gene = json.load(f)
    pipeline = BERN2AngelPipeline(mesh_id_map, ncbi_gene)

    while True:
        text = input(">")
        print("-----")
        for e in pipeline(text):
            print(e)
        print("------")
