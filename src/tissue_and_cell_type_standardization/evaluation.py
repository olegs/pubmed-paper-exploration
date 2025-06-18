from sklearn.metrics import accuracy_score, f1_score

def synonym_f1_score(predicted_synonyms, true_synonyms, mesh_id_map):
    predicted_synonyms = map(lambda x: x.strip().lower(), predicted_synonyms)
    predicted_ids = [mesh_id_map[predicted_synonym] if predicted_synonym in mesh_id_map else predicted_synonym for predicted_synonym in predicted_synonyms]
    true_ids = [mesh_id_map[true_synonym] if true_synonym in mesh_id_map else true_synonym for true_synonym in true_synonyms]
    return f1_score(predicted_ids, true_ids, average="macro")

def are_terms_same(term1, term2, mesh_id_map):
    term1_id = mesh_id_map.get(term1, term1)
    term2_id = mesh_id_map.get(term2, term2)
    return term1_id == term2_id

if __name__ == "__main__":
    import pandas as pd
    from src.tissue_and_cell_type_standardization.get_standard_name import get_standard_name
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    from src.tissue_and_cell_type_standardization.get_standard_name_spacy import create_entity_linking_pipeline_with_ner
    from src.tissue_and_cell_type_standardization.standardization_resources import StandardizationResources
    from src.tissue_and_cell_type_standardization.get_standard_name_gilda import get_standard_name_gilda
    from src.tissue_and_cell_type_standardization.get_standard_name_spacy import get_standard_name_spacy
    from sklearn.model_selection import train_test_split

    nlp = create_entity_linking_pipeline_with_ner()
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    resources = StandardizationResources(mesh_lookup, nlp)

    mesh_term_df = pd.read_csv("mesh_terms.csv")
    mesh_id_map = dict(zip(mesh_term_df["term"], mesh_term_df["mesh_id"]))
    assert synonym_f1_score(["yellow marrow", "heart", "brain"], ["bone marrow", "heart", "bone"], mesh_id_map) - 2/3 <=0.01
    test_tissues_and_cell_types_df = pd.read_csv("test_synonyms.csv")
    test_tissues_and_cell_types_df = test_tissues_and_cell_types_df[test_tissues_and_cell_types_df["synonym"] != "UNKNOWN"]
    x_train, x_test, y_train, y_test = train_test_split(test_tissues_and_cell_types_df["tissue_or_cell_type"], test_tissues_and_cell_types_df["synonym"], test_size=0.2, random_state=42)
    x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=0.25, random_state=42)
    pred_train = [get_standard_name(term, resources) for term in x_train]
    pred_val = [get_standard_name(term, resources) for term in x_val]
    
    
    print("Gilda + spacy")
    print("Training accuracy:", synonym_f1_score(pred_train, y_train, mesh_id_map))
    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) + list(pred_val), list(y_train) + list(y_val), mesh_id_map))


    print("spacy")
    pred_train = [get_standard_name_spacy(term, resources.nlp) for term in x_train]
    pred_val = [get_standard_name_spacy(term, resources.nlp) for term in x_val]
    print("Training accuracy:", synonym_f1_score(pred_train, y_train, mesh_id_map))
    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) + list(pred_val), list(y_train) + list(y_val), mesh_id_map))

    print("gilda")
    pred_train = [get_standard_name_gilda(term, resources.mesh_lookup) or term for term in x_train]
    pred_val = [get_standard_name_gilda(term, resources.mesh_lookup) or term for term in x_val]
    print("Training accuracy:", synonym_f1_score(pred_train, y_train, mesh_id_map))
    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) + list(pred_val), list(y_train) + list(y_val), mesh_id_map))
