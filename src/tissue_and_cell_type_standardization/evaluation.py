from collections.abc import Callable
from sklearn.metrics import f1_score
import logging
from src.training_data_gathering.validate_data import is_synonym_valid
import pandas as pd
from src.tissue_and_cell_type_standardization.get_standard_name import get_standard_name
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
from src.tissue_and_cell_type_standardization.get_standard_name_spacy import create_entity_linking_pipeline_with_ner
from src.tissue_and_cell_type_standardization.standardization_resources import StandardizationResources
from src.tissue_and_cell_type_standardization.get_standard_name_gilda import get_standard_name_gilda
from src.tissue_and_cell_type_standardization.get_standard_name_spacy import get_standard_name_spacy
from src.tissue_and_cell_type_standardization.get_standard_name_fasttext import FastTextParser
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import is_mesh_term_in_anatomy_or_cancer
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def synonym_f1_score(predicted_synonyms, true_synonyms, mesh_id_map):
    predicted_synonyms = map(lambda x: x.strip().lower(), predicted_synonyms)
    predicted_ids = [mesh_id_map[predicted_synonym]
                     if predicted_synonym in mesh_id_map else predicted_synonym for predicted_synonym in predicted_synonyms]
    true_ids = [mesh_id_map[true_synonym]
                if true_synonym in mesh_id_map else true_synonym for true_synonym in true_synonyms]
    return f1_score(predicted_ids, true_ids, average="macro", labels=list(set(true_ids)))


def export_errors(x_val, y_val, pred_val, output_path, mesh_id_map):
    errors_data = []
    for i in range(len(x_val)):
        original_term = x_val.values[i]
        true_synonym = y_val.values[i]
        predicted_synonym = pred_val[i]

        # Use are_terms_same for comparison, which handles Mesh ID mapping
        if not are_terms_same(true_synonym, predicted_synonym, mesh_id_map):
            error = {
                "Original_Term": original_term,
                "True_Synonym": true_synonym,
                "True_Synonym_Mesh_ID": mesh_id_map.get(true_synonym.strip().lower(), true_synonym.strip().lower()),
                "Predicted_Synonym": predicted_synonym,
                "Predicted_Synonym_Mesh_ID": mesh_id_map.get(predicted_synonym.strip().lower(), predicted_synonym.strip().lower()),
                "Ontology": "MeSH"
            }
            assert error["True_Synonym_Mesh_ID"] != error["Predicted_Synonym_Mesh_ID"]
            errors_data.append(error)

    if errors_data:
        errors_df = pd.DataFrame(errors_data)
        errors_df.to_csv(output_path, index=False)
        print(f"Errors exported to {output_path}")
    else:
        print("No errors found for the model on the validation set.")


def are_terms_same(term1, term2, mesh_id_map):
    term1_id = mesh_id_map.get(term1.strip().lower(), term1)
    term2_id = mesh_id_map.get(term2.strip().lower(), term2)
    return term1_id == term2_id


def export_dataset(x, y, output_path):
    data = []
    for i in range(len(x)):
        data.append({
            "Tissue/Cell type": x.values[i],
            "True synonym": y.values[i],
            "Ontology": "MeSH"
        })
    validtion_df = pd.DataFrame(data)
    validtion_df.to_csv(output_path)


def model_f1_score(model: Callable, x, y, mesh_id_map, errors_output_path):
    predictions = []

    for term in tqdm(x):
        try:
            predictions.append(model(term) or "UNPARSED")
        except ValueError:
            predictions.append("UNPARSED")

    export_errors(x, y, predictions,
                  errors_output_path, mesh_id_map)
    return (synonym_f1_score(predictions, y, mesh_id_map), predictions)


def evaluate(model: Callable, model_name: str, x_train, y_train, x_val, y_val, mesh_id_map):
    print(model_name)
    f1_train, pred_train = model_f1_score(model, x_train, y_train, mesh_id_map, f"errors_train_{model_name}.csv")
    print("Training F1 score:", f1_train)
    f1_validation, pred_val = model_f1_score(model, x_val, y_val, mesh_id_map, f"errors_validation_{model_name}.csv")
    print("Validation F1 score:", f1_validation)
    f1_total = synonym_f1_score(list(pred_train) +
          list(pred_val), list(y_train) + list(y_val), mesh_id_map)
    print("Total F1 score:", f1_total)



if __name__ == "__main__":
    logging.disable(logging.WARN)

    nlp = create_entity_linking_pipeline_with_ner()
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    resources = StandardizationResources(mesh_lookup, nlp)

    mesh_id_map = {key.strip().lower(): entry.id
                   for key, entry in mesh_lookup.items()}
    assert abs(synonym_f1_score(["yellow marrow", "heart", "brain", "heart"], [
                            "bone marrow", "heart", "bone", "heart"], mesh_id_map) - 2/3) <= 0.01
    assert abs(synonym_f1_score(["yellow marrow", "heart", "brain", "heart"], [
                            "bone marrow", "heart", "UNPARSED", "heart"], mesh_id_map) - 2/3) <= 0.01

    test_tissues_and_cell_types_df = pd.read_csv("test_synonyms.csv")
    test_tissues_and_cell_types_df = test_tissues_and_cell_types_df[
        test_tissues_and_cell_types_df["synonym"] != "UNKNOWN"]
    test_tissues_and_cell_types_df = test_tissues_and_cell_types_df[
        test_tissues_and_cell_types_df["synonym"].apply(lambda synonym: is_synonym_valid(synonym, mesh_lookup))]

    x_train, x_test, y_train, y_test = train_test_split(
        test_tissues_and_cell_types_df["tissue_or_cell_type"], test_tissues_and_cell_types_df["synonym"], test_size=0.2, random_state=42)
    x_train, x_val, y_train, y_val = train_test_split(
        x_train, y_train, test_size=0.25, random_state=42)

    export_dataset(x_train, y_train, "train.csv")
    export_dataset(x_val, y_val, "validation.csv")
    export_dataset(x_test, y_test, "test.csv")

    model = lambda term: get_standard_name(term, resources)
    evaluate(model, "gilda_plus_spacy", x_train, y_train, x_val, y_val, mesh_id_map)

    model = lambda term: get_standard_name_spacy(term, resources.nlp, resources.mesh_lookup)
    evaluate(model, "spacy", x_train, y_train, x_val, y_val, mesh_id_map)

    model = lambda term: get_standard_name_gilda(term, resources.mesh_lookup)
    evaluate(model, "gilda", x_train, y_train, x_val, y_val, mesh_id_map)

    filtered_mesh_lookup = {key: value for key, value in mesh_lookup.items(
    ) if is_mesh_term_in_anatomy_or_cancer(key, mesh_lookup)}
    fasttext_parser = FastTextParser(
        "BioWordVec_PubMed_MIMICIII_d200.vec.bin", filtered_mesh_lookup)
    model = lambda term: fasttext_parser.get_standard_name(term)[0]
    evaluate(model, "fasttext", x_train, y_train, x_val, y_val, mesh_id_map)

    model = lambda term: fasttext_parser.get_standard_name_reranked(term)[0]
    evaluate(model, "reranked_fasttext", x_train, y_train, x_val, y_val, mesh_id_map)
