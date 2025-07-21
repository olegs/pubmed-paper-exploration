from typing import Dict, Set
import gilda


def get_standard_name_gilda(name: str, mesh_lookup: Dict[str, Set[str]]) -> str | None:
    """
    Gets the standard name for a tissue or cell type using the Gilda NER 
    package.

    :param name: Tissue or cell type name to standardize.
    :param mesh_lookup: A pre-built dictionary mapping valid MeSH terms to tree 
        numbers (see build_mesh_lookup).

    :return: Standardized name of the tissue or cell type or None if a
    standardized name cannot be determined. All returned entities will be contained in mesh_lookup.
    """
    annotations = gilda.annotate(name)
    matches = [match for annotation in annotations for match in annotation.matches]
    sorted_matches = sorted(matches, key=lambda m: m.score, reverse=True)

    for match in sorted_matches:
        standard_name = match.term.entry_name
        if match.term.db == "MESH" and (standard_name.strip().lower() in mesh_lookup):
            return standard_name

    return None


if __name__ == "__main__":
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    print("Mouse fat", get_standard_name_gilda("mouse fat", mesh_lookup))
    print("that thing", get_standard_name_gilda(
        "whole body of single-housed females at 9 dph", mesh_lookup))
    print("normal lung", get_standard_name_gilda(
        "normal lung tissue", mesh_lookup))
    print("penumbras", get_standard_name_gilda(
        "penumbras tissue of brains", mesh_lookup))
    print("rectus", get_standard_name_gilda(
        "left rectus abdominus", mesh_lookup))
    print("gut", get_standard_name_gilda("gut", mesh_lookup))
    print("trachea", get_standard_name_gilda("trachea", mesh_lookup))
    print("mixture", get_standard_name_gilda(
        "10% human blood, 90% mouse fat", mesh_lookup))
    print("cardiac", get_standard_name_gilda("cardiac", mesh_lookup))
