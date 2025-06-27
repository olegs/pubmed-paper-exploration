import requests
from src.ingestion.rate_limit import RateLimited
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup, is_mesh_term_in_anatomy_or_cancer


@RateLimited(max_per_second=3)
def get_standard_name_bern2(text, mesh_id_map, mesh_lookup, url="http://bern2.korea.ac.kr/plain") -> str | None:
    response = requests.post(url, json={'text': text}).json()
    candidate_ids = []
    for annotation in sorted(response["annotations"], key=lambda ann: ann["prob"]):
        annotation_ids = list(filter(lambda id: id.startswith("mesh"), annotation["id"]))
        annotation_ids = [ann_id[len("mesh:"):] for ann_id in annotation_ids]
        candidate_ids += annotation_ids
    
    candidate_terms = [mesh_id_map[candidate_id] for candidate_id in candidate_ids]
    candidate_terms = list(filter(lambda term: is_mesh_term_in_anatomy_or_cancer(term, mesh_lookup), candidate_terms))
    return candidate_terms[0] if candidate_terms else None





if __name__ == '__main__':
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    mesh_id_map = {entry.id: key.strip().lower()
                   for key, entry in mesh_lookup.items()}

    while True:
        text = input(">")
        print(get_standard_name_bern2(text, mesh_id_map, mesh_lookup))