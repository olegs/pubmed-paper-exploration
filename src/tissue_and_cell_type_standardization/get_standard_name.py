from typing import Dict, Set
from functools import lru_cache
from src.tissue_and_cell_type_standardization.get_standard_name_gilda import get_standard_name_gilda
from src.tissue_and_cell_type_standardization.get_standard_name_spacy import get_standard_name_spacy
from src.tissue_and_cell_type_standardization.standardization_resources import StandardizationResources


def preprocess_tissue_name(name: str) -> str:
    # TODO: Expand abbreviations
    return name.replace("_", " ")


@lru_cache(10000)
def get_standard_name(name: str, resources: StandardizationResources) -> str | None:
    """
    Standardizes the name for a tissue or cell type.

    :param name: Tissue or cell type name to standardize
    :param resources: An instance of StandardizationResources containing
                      the MeSH dictionary and the spacy pipeline.

    :return: Standardized name of the tissue or None if the
    standardized name cannot be determined.
    """
    name = preprocess_tissue_name(name)
    gilda_name = get_standard_name_gilda(name, resources.mesh_lookup)
    if gilda_name:
        return gilda_name
    return get_standard_name_spacy(
        name, resources.nlp, resources.mesh_lookup)


if __name__ == "__main__":
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    from src.tissue_and_cell_type_standardization.get_standard_name_spacy import create_entity_linking_pipeline_with_ner
    nlp = create_entity_linking_pipeline_with_ner()
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    resources = StandardizationResources(mesh_lookup, nlp)

    print("Mouse fat", get_standard_name("mouse fat", resources))
    print("that thing", get_standard_name(
        "whole body of single-housed females at 9 dph", resources))
    print("normal lung", get_standard_name(
        "normal lung tissue", resources))
    print("penumbras", get_standard_name(
        "penumbras tissue of brains", resources))
    print("rectus", get_standard_name("left rectus abdominus", resources))
    print("gut", get_standard_name("gut", resources))
    print("trachea", get_standard_name("trachea", resources))
    print("mixture", get_standard_name(
        "10% human blood, 90% mouse fat", resources))
    print("cardiac", get_standard_name("cardiac", resources))
    print("lung cells", get_standard_name("lung cells", resources))
