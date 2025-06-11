import gilda
from src.tissue_parsing.is_mesh_term_in_anatomy_or_disease import is_mesh_term_in_anatomy_or_disease

def get_standard_name_gilda(name, mesh_lookup):
    annotations = gilda.annotate(name)
    matches = [match for annotation in annotations for match in annotation.matches]
    sorted_matches = sorted(matches, key=lambda m: m.score)
    for match in sorted_matches:
        standard_name = match.term.entry_name
        if match.term.db == "MESH" and is_mesh_term_in_anatomy_or_disease(standard_name, mesh_lookup):
            return standard_name
    
    return None


if __name__ == "__main__":
    from src.tissue_parsing.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    print("Mouse fat", get_standard_name_gilda("mouse fat", mesh_lookup))
    print("that thing", get_standard_name_gilda("whole body of single-housed females at 9 dph", mesh_lookup))
    print("normal lung", get_standard_name_gilda("normal lung tissue", mesh_lookup))
    print("penumbras", get_standard_name_gilda("penumbras tissue of brains", mesh_lookup))
    print("rectus", get_standard_name_gilda("left rectus abdominus", mesh_lookup))
    print("gut", get_standard_name_gilda("gut", mesh_lookup))
    print("trachea", get_standard_name_gilda("trachea", mesh_lookup))
    print("mixture", get_standard_name_gilda("10% human blood, 90% mouse fat", mesh_lookup))
    print("cardiac", get_standard_name_gilda("cardiac", mesh_lookup))

