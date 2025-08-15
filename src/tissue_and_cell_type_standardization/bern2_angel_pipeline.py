from typing import Dict
from src.tissue_and_cell_type_standardization.get_standard_name_bern2 import BERN2Pipeline
from typing import Dict
from src.tissue_and_cell_type_standardization.angel_normalizer import ANGELMeshNormalizer
from src.tissue_and_cell_type_standardization.entity_normalizer import NormalizationResult


class BERN2AngelPipeline(BERN2Pipeline):
    def __init__(self, mesh_id_map: Dict[str, str], ncbi_gene: Dict[str, str], url: str="http://localhost:8888/plain"):
        super().__init__(mesh_id_map, ncbi_gene, url)
        self.angel = ANGELMeshNormalizer({value: key for key, value in mesh_id_map.items()})

    def preprocess_annotations(self, annotations, text):
        for annotation in annotations:
            if "CUI-less" in annotation["id"]:
                normalization = self.angel.normalize_with_context(text, annotation["span"]["begin"], annotation["span"]["end"])
                annotation["id"].append("mesh:" + normalization.cui)
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
