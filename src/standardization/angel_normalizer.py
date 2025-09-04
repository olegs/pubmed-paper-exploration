from ANGEL.run_sample import run_sample
from ANGEL.utils import get_config
from src.standardization.entity_normalizer import EntityNormalizer, NormalizationResult


class ANGELMeshNormalizer(EntityNormalizer):
    def __init__(self, mesh_lookup, candidates=None):
        self.mesh_lookup = mesh_lookup
        self.config = get_config()
        self.candidates = candidates or list(self.mesh_lookup.keys())

    def normalize_entity(self, entity: str):
        input_sentence = f"START {entity} END"
        prefix_sentence = f"{entity} is"
        if entity in self.mesh_lookup:
            mesh_entry = self.mesh_lookup[entity.strip().lower()]
            return NormalizationResult(entity, mesh_entry.term, "MeSH", mesh_entry.id, 1.0)

        standard_name = run_sample(self.config, input_sentence, prefix_sentence, self.candidates).strip()
        return NormalizationResult(entity, standard_name, "MeSH", self.mesh_lookup[standard_name].id, 1.0)

    def normalize_with_context(self, context: str, entity_begin: int, entity_end: int) -> NormalizationResult:
        entity = context[entity_begin:entity_end]
        input_sentence = context[:entity_begin] + "START " + entity + " END" + context[entity_end:]
        prefix_sentence = f"{entity} is"

        standard_name = run_sample(self.config, input_sentence, prefix_sentence, self.candidates).strip()
        return NormalizationResult(entity, standard_name, "MeSH", self.mesh_lookup[standard_name].id, 1.0)


if __name__ == "__main__":
    from src.mesh.mesh_vocabulary import build_mesh_lookup

    mesh_lookup = build_mesh_lookup("desc2025.xml")

    normalizer = ANGELMeshNormalizer(mesh_lookup)

    input_sentence = "T cells from CRC patients were sorted, profiled by Smart-seq2 and sequenced on HiSeq4000. Based on FACS analysis, single cells of different subtypes, including START CD8+ T cells END (CD3+ and CD8+), T helper cells (CD3+, CD4+ and CD25-), and regulatory T cells (CD3+, CD4+ and CD25high) were sorted to perform RNA sequencing. The categories ?""sampleType"" column in the SAMPLES section? contain PTC(CD8+ T cells from peripheral blood), NTC(CD8+ T cells from adjacent normal colonrectal tissues) ,TTC (CD8+ T cells from tumor), PTH(CD3+, CD4+ and CD25- T cells from peripheral blood), NTH(CD3+, CD4+ and CD25- T cells from adjacent normal colonrectal tissues), TTH(CD3+, CD4+ and CD25- T cells from tumor), PTR(CD3+, CD4+ and CD25high T cells from peripheral blood), NTR(CD3+, CD4+ and CD25high T cells from adjacent normal colonrectal tissues), TTR(CD3+, CD4+ and CD25high T cells from tumor), PTY(CD3+, CD4+ and CD25mediate T cells from peripheral blood), NTY(CD3+, CD4+ and CD25mediate T cells from adjacent normal colonrectal tissues), TTY(CD3+, CD4+ and CD25medate T cells from tumor), PP7(CD3+, CD4+ T cells from peripheral blood), NP7(CD3+, CD4+ T cells from adjacent normal colonrectal tissues), TP7(CD3+, CD4+ T cells from tumor)."
    prefix_sentence = "CD8+ T cells is"

    standard_name = run_sample(normalizer.config, input_sentence, prefix_sentence, normalizer.candidates)[0][0].strip()
    print(standard_name)

    while True:
        term = input("> ")
        print(normalizer(term))
