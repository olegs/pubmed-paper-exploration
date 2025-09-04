import pandas as pd

from src.mesh.mesh_vocabulary import build_mesh_lookup


def is_synonym_valid(synonym, mesh_lookup):
    if synonym in ["UNKNOWN", "whole organism"]:
        return True
    return synonym.strip().lower() in mesh_lookup


if __name__ == "__main__":
    df = pd.read_csv("test_synonyms.csv")
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    mesh_lookup = {key.strip().lower(): value for key, value in mesh_lookup.items()}
    valid = True
    for term, synonym in zip(df["tissue_or_cell_type"], df["synonym"]):
        if not is_synonym_valid(synonym, mesh_lookup):
            print(f'In "{term}","{synonym}"; "{synonym}" not a mesh term on the list of MeSH terms.')
            valid = False

    if valid:
        print("Data valid :D")
