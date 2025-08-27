from typing import Dict
from src.standardization.angel_normalizer import ANGELMeshNormalizer
from src.standardization.get_standard_name_fasttext import FasttextNormalizer
from src.standardization.entity_normalizer import NormalizationResult
from src.ANGEL.run_sample import run_sample


class ANGELFasttextMeshNormalizer(ANGELMeshNormalizer):
    def __init__(self, mesh_lookup):
        super().__init__(mesh_lookup, None)
        self.fasttext = FasttextNormalizer(
            "BioWordVec_PubMed_MIMICIII_d200.vec.bin", mesh_lookup)

    def _normalize(self, input_sentence, entity):
        prefix_sentence = f"{entity} is"
        candidates = []
        try:
            candidates = self.fasttext.get_standard_name_with_score(entity, 50)
        except Exception as e:
            print(e)
        if candidates and (candidates[0][1] < 0.001):
            print("Found exact match")
            standard_name = candidates[0][0]
            return NormalizationResult(entity, standard_name, "MeSH", self.mesh_lookup[standard_name].id, 1.0)
        elif candidates:
            print(f"First candidate for {entity}:", candidates[0])


        candidates = [c[0] for c in candidates]
        if not candidates:
            candidates = [key for key in self.mesh_lookup.keys()]
            print(candidates[0])
        standard_name = run_sample(
            self.config, input_sentence, prefix_sentence, candidates).strip()
        return NormalizationResult(entity, standard_name, "MeSH", self.mesh_lookup[standard_name].id, 1.0)

    def normalize_entity(self, entity: str) -> NormalizationResult:
        input_sentence = f"START {entity} END"
        return self._normalize(input_sentence, entity)

    def normalize_with_context(self, context: str, entity_begin: int, entity_end: int) -> NormalizationResult:
        entity = context[entity_begin:entity_end]
        input_sentence = context[:entity_begin] + \
            "START " + entity + " END" + context[entity_end:]
        return self._normalize(input_sentence, entity)


if __name__ == "__main__":
    from src.standardization.mesh_vocabulary import build_mesh_lookup
    mesh_lookup = build_mesh_lookup("desc2025.xml")

    mesh_id_map = {key.strip().lower(): entry.id
                   for key, entry in mesh_lookup.items()}

    normalizer = ANGELFasttextMeshNormalizer(mesh_id_map)

    #print(normalizer.normalize_with_context(""))

    while True:
        term = input("> ")
        print(normalizer(term))
