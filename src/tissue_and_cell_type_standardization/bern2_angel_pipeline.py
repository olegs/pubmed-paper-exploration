from typing import Dict
from src.tissue_and_cell_type_standardization.get_standard_name_bern2 import BERN2Pipeline
from typing import Dict
from src.tissue_and_cell_type_standardization.angel_normalizer import ANGELMeshNormalizer


class BERN2AngelPipeline(BERN2Pipeline):
    def __init__(self, mesh_lookup, ncbi_gene: Dict[str, str], url: str="http://localhost:8888/plain", must_normalize_to_mesh=False):
        mesh_id_to_term_map = {entry.id: key.strip().lower()
                               for key, entry in mesh_lookup.items()}
        super().__init__(mesh_id_to_term_map, ncbi_gene, url)
        self.angel = ANGELMeshNormalizer(mesh_lookup)
        self.must_normalize_to_mesh = must_normalize_to_mesh
        self.angel_cache = {}

    def preprocess_annotations(self, annotations, text):
        for annotation in annotations:
            if "CUI-less" in annotation["id"] or (self.must_normalize_to_mesh and not any(term_id.startswith("mesh:") for term_id in annotation["id"])):
                mention = annotation["mention"]
                mention = mention.strip().lower()
                mesh_id = ""
                if mention in self.angel_cache:
                    mesh_id = self.angel_cache[mention].cui
                else:
                    normalization = self.angel.normalize_entity(mention)
                    mesh_id = normalization.cui
                    self.angel_cache[mention] = normalization

                annotation["id"].append("mesh:" + mesh_id)
        return annotations


if __name__=="__main__":
    import json
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
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
