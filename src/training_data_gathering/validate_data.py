from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup, is_mesh_term_in_anatomy_or_cancer
import pandas as pd

def is_synonym_valid(synonym, mesh_lookup):
    if synonym in ["UNKNOWN", "whole organism"]:
        return True
    if synonym.strip().lower() not in mesh_lookup or not is_mesh_term_in_anatomy_or_cancer(synonym, mesh_lookup):
        return False
    return True

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