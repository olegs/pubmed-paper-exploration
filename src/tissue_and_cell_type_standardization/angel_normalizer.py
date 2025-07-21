from typing import Dict
from src.tissue_and_cell_type_standardization.entity_normalizer import EntityNormalizer, NormalizationResult
from src.ANGEL.run_sample import run_sample 
from src.ANGEL.utils import get_config

class ANGELMeshNormalizer(EntityNormalizer):
    def __init__(self, mesh_term_to_id_map: Dict[str, str]):
        self.mesh_term_to_id_map = mesh_term_to_id_map
        self.config = get_config()
        self.candidates = list(self.mesh_term_to_id_map.keys())

    def normalize_entity(self, entity: str):
        input_sentence = f"START {entity} END"
        prefix_sentence = f"{entity} is"
        
        standard_name = run_sample(self.config, input_sentence, prefix_sentence, self.candidates).strip()
        return NormalizationResult(entity, standard_name, "MeSH", self.mesh_term_to_id_map[standard_name], 1.0)


if __name__ == "__main__":
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    mesh_lookup = build_mesh_lookup("desc2025.xml")

    mesh_id_map = {key.strip().lower(): entry.id
                   for key, entry in mesh_lookup.items()}

    normalizer = ANGELMeshNormalizer(mesh_id_map)

    while True:
        term = input("> ")
        print(normalizer(term))
