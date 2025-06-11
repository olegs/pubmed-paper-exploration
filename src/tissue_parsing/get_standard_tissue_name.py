from typing import Dict, Set
from src.tissue_parsing.parse_tissue_gilda import get_standard_name_gilda
from src.tissue_parsing.parse_tissue import get_standard_name_spacy

def preprocess_tissue_name(name: str) -> str:
    return name.replace("_", " ")

def get_standard_tissue_name(name: str, mesh_lookup: Dict[str, Set[str]], nlp) -> str | None:
    """
    Standardizes the name for a tissue or cell type.

    :param name: Tissue or cell type name to standardize
    :param mesh_lookup: A pre-built dictionary mapping MeSH terms to tree 
        numbers (see build_mesh_lookup).
    :param nlp: Scispacy NER and entity linking pipeline created by
    create_entity_linking_pipline_with_ner.

    :return: Standardized name of the tissue or the input name if the
    standardized name cannot be determined.
    """
    name = preprocess_tissue_name(name)
    gilda_name = get_standard_name_gilda(name, mesh_lookup)
    if gilda_name:
        return gilda_name
    
    return get_standard_name_spacy(name, nlp)

if __name__ == "__main__":
    from src.tissue_parsing.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    from src.tissue_parsing.parse_tissue import create_entity_linking_pipeline_with_ner
    nlp = create_entity_linking_pipeline_with_ner() 
    mesh_lookup = build_mesh_lookup("desc2025.xml")

    print("Mouse fat", get_standard_tissue_name("mouse fat", mesh_lookup, nlp))
    print("that thing", get_standard_tissue_name("whole body of single-housed females at 9 dph", mesh_lookup, nlp))
    print("normal lung", get_standard_tissue_name("normal lung tissue", mesh_lookup, nlp))
    print("penumbras", get_standard_tissue_name("penumbras tissue of brains", mesh_lookup, nlp))
    print("rectus", get_standard_tissue_name("left rectus abdominus", mesh_lookup, nlp))
    print("gut", get_standard_tissue_name("gut", mesh_lookup, nlp))
    print("trachea", get_standard_tissue_name("trachea", mesh_lookup, nlp))
    print("mixture", get_standard_tissue_name("10% human blood, 90% mouse fat", mesh_lookup, nlp))
    print("cardiac", get_standard_tissue_name("cardiac", mesh_lookup, nlp))
    print("lung cells", get_standard_tissue_name("lung cells", mesh_lookup, nlp))