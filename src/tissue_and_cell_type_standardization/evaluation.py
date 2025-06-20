from sklearn.metrics import accuracy_score, f1_score
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
from gensim.models import KeyedVectors
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def synonym_f1_score(predicted_synonyms, true_synonyms, mesh_id_map):
    predicted_synonyms = map(lambda x: x.strip().lower(), predicted_synonyms)
    predicted_ids = [mesh_id_map[predicted_synonym]
                     if predicted_synonym in mesh_id_map else predicted_synonym for predicted_synonym in predicted_synonyms]
    true_ids = [mesh_id_map[true_synonym]
                if true_synonym in mesh_id_map else true_synonym for true_synonym in true_synonyms]
    return f1_score(predicted_ids, true_ids, average="macro")


def export_errors(x_val, y_val, pred_val, output_path):
    errors_data = []
    for i in range(len(x_val)):
        original_term = x_val.values[i]
        true_synonym = y_val.values[i]
        predicted_synonym = pred_val[i]

        # Use are_terms_same for comparison, which handles Mesh ID mapping
        if not are_terms_same(original_term, predicted_synonym, mesh_id_map):
            errors_data.append({
                "Original_Term": original_term,
                "True_Synonym": true_synonym,
                "True_Synonym_Mesh_ID": mesh_id_map.get(true_synonym.strip().lower(), true_synonym.strip().lower()),
                "Predicted_Synonym": predicted_synonym,
                "Predicted_Synonym_Mesh_ID": mesh_id_map.get(predicted_synonym.strip().lower(), predicted_synonym.strip().lower())
            })

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
    for i in range(len(pred_val)):
       data.append({
            "Tissue/Cell type": x.values[i],
            "True synonym": y.values[i],
    })
    validtion_df = pd.DataFrame(data)
    validtion_df.to_csv(output_path)


if __name__ == "__main__":
    logging.disable(logging.WARN)


    nlp = create_entity_linking_pipeline_with_ner()
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    resources = StandardizationResources(mesh_lookup, nlp)

    mesh_id_map = {key.strip().lower(): entry.id
                   for key, entry in mesh_lookup.items()}
    assert synonym_f1_score(["yellow marrow", "heart", "brain"], [
                            "bone marrow", "heart", "bone"], mesh_id_map) - 2/3 <= 0.01

    test_tissues_and_cell_types_df = pd.read_csv("test_synonyms.csv")
    test_tissues_and_cell_types_df = test_tissues_and_cell_types_df[
        test_tissues_and_cell_types_df["synonym"] != "UNKNOWN"]
    test_tissues_and_cell_types_df = test_tissues_and_cell_types_df[
        test_tissues_and_cell_types_df["synonym"].apply(lambda synonym: is_synonym_valid(synonym, mesh_lookup))]

    x_train, x_test, y_train, y_test = train_test_split(
        test_tissues_and_cell_types_df["tissue_or_cell_type"], test_tissues_and_cell_types_df["synonym"], test_size=0.2, random_state=42)
    x_train, x_val, y_train, y_val = train_test_split(
        x_train, y_train, test_size=0.25, random_state=42)
    pred_train = [get_standard_name(term, resources) for term in x_train]
    pred_val = [get_standard_name(term, resources) for term in x_val]

    export_dataset(x_train, y_train, "train.csv")
    export_dataset(x_val, y_val, "validation.csv")
    export_dataset(x_test, y_test, "test.csv")




    print("Gilda + spacy")
    print("Training accuracy:", synonym_f1_score(
        pred_train, y_train, mesh_id_map))
    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) +
          list(pred_val), list(y_train) + list(y_val), mesh_id_map))
    export_errors(x_val, y_val, pred_val, "gilda_spacy_errors.csv")

    print("spacy")
    pred_train = [get_standard_name_spacy(
        term, resources.nlp, resources.mesh_lookup) for term in x_train]
    pred_val = [get_standard_name_spacy(
        term, resources.nlp, resources.mesh_lookup) for term in x_val]
    print("Training accuracy:", synonym_f1_score(
        pred_train, y_train, mesh_id_map))
    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) +
          list(pred_val), list(y_train) + list(y_val), mesh_id_map))
    export_errors(x_val, y_val, pred_val, "gilda_errors.csv")

    print("gilda")
    pred_train = [get_standard_name_gilda(
        term, resources.mesh_lookup) or term for term in x_train]
    pred_val = [get_standard_name_gilda(
        term, resources.mesh_lookup) or term for term in x_val]
    print("Training accuracy:", synonym_f1_score(
        pred_train, y_train, mesh_id_map))
    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) +
          list(pred_val), list(y_train) + list(y_val), mesh_id_map))
    export_errors(x_val, y_val, pred_val, "spacy_errors.csv")

    print("fasttext")
    from src.tissue_and_cell_type_standardization.get_standard_name_fasttext import preprocess
    filtered_mesh_lookup = {key: value for key, value in mesh_lookup.items(
    ) if is_mesh_term_in_anatomy_or_cancer(key, mesh_lookup)}
    fasttext_parser = FastTextParser(
        "BioWordVec_PubMed_MIMICIII_d200.vec.bin", filtered_mesh_lookup)
    pred_train = []
    pred_val = []

    for term in tqdm(x_train):
        try:
            pred_train.append(fasttext_parser.get_standard_name(
                term)[0])
        except ValueError:
            pred_train.append("UNPARSED")
    print("Training accuracy:", synonym_f1_score(
        pred_train, y_train, mesh_id_map))

    for term in tqdm(x_val):
        try:
            pred_val.append(fasttext_parser.get_standard_name(
                term)[0])
        except ValueError:
            pred_val.append("UNPARSED")

    print("Validation accuracy:", synonym_f1_score(pred_val, y_val, mesh_id_map))
    print("Total accuracy", synonym_f1_score(list(pred_train) +
          list(pred_val), list(y_train) + list(y_val), mesh_id_map))
    export_errors(x_val, y_val, pred_val, "fasttext_model_errors.csv")
