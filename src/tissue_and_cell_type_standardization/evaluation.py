from collections.abc import Callable
from argparse import ArgumentParser
from sklearn.metrics import f1_score, recall_score, precision_score
import logging
from src.training_data_gathering.validate_data import is_synonym_valid
import pandas as pd
from src.tissue_and_cell_type_standardization.get_standard_name import get_standard_name
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup, is_term_in_one_of_categories
from src.tissue_and_cell_type_standardization.get_standard_name_spacy import create_entity_linking_pipeline_with_ner
from src.tissue_and_cell_type_standardization.standardization_resources import StandardizationResources
from src.tissue_and_cell_type_standardization.get_standard_name_gilda import get_standard_name_gilda
from src.tissue_and_cell_type_standardization.get_standard_name_spacy import get_standard_name_spacy
from src.tissue_and_cell_type_standardization.get_standard_name_fasttext import FastTextParser, FasttextNormalizer
from src.tissue_and_cell_type_standardization.get_standard_name_bern2 import get_standard_name_bern2, BERN2Recognizer
from src.tissue_and_cell_type_standardization.ner_nen_pipeline import NER_NEN_Pipeline
from src.tissue_and_cell_type_standardization.angel_normalizer import ANGELMeshNormalizer
from tqdm import tqdm


def export_predictions(x_val, y_val, pred_val, output_path, mesh_id_map):
    predictions = [{
        "Original_Term": original_term,
        "True_Synonym": true_synonym,
        "True_Synonym_Mesh_ID": mesh_id_map.get(true_synonym.strip().lower(), true_synonym.strip().lower()),
        "Predicted_Synonym": predicted_synonym,
        "Predicted_Synonym_Mesh_ID": mesh_id_map.get(predicted_synonym.strip().lower(), predicted_synonym.strip().lower()),
        "Ontology": "MeSH"
    } for original_term, true_synonym, predicted_synonym in zip(x_val, y_val, pred_val)]

    pd.DataFrame(predictions).to_csv(output_path, index=False)


def export_errors(x_val, y_val, pred_val, output_path, mesh_id_map):
    errors = [(x, y, pred) for x, y, pred in zip(
        x_val, y_val, pred_val) if not are_terms_same(y, pred, mesh_id_map)]

    if not errors:
        print("No errors found for the model on the validation set.")
        return

    x_val, y_val, pred_val = zip(*errors)
    export_predictions(x_val, y_val, pred_val, output_path, mesh_id_map)
    print(f"Errors exported to {output_path}")


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


def predict(model: Callable, x, mesh_id_map):
    predictions = []

    for term in tqdm(x):
        try:
            predictions.append(model(term) or "UNPARSED")
        except ValueError:
            predictions.append("UNPARSED")

    predictions = list(map(lambda x: x.strip().lower(), predictions))
    predicted_ids = [mesh_id_map[predicted_synonym]
                     if predicted_synonym in mesh_id_map else predicted_synonym for predicted_synonym in predictions]
    return (predictions, predicted_ids)


def evaluate(model: Callable, model_name: str, x, y, mesh_id_map):
    y_pred, y_pred_ids = predict(model, x, mesh_id_map)
    y_ids = [mesh_id_map[true_synonym]
             if true_synonym in mesh_id_map else true_synonym for true_synonym in y]
    f1 = f1_score(y_ids, y_pred_ids, average="macro", labels=list(set(y_ids)))
    recall = recall_score(
        y_ids, y_pred_ids, average="macro", labels=list(set(y_ids)))
    precision = precision_score(
        y_ids, y_pred_ids, average="macro", labels=list(set(y_ids)))

    print("F1 score:", f1)
    print("Precision:", precision)
    print("Recall:", recall)

    export_predictions(
        x, y, y_pred, f"predictions_{model_name}.csv", mesh_id_map)
    export_errors(x, y, y_pred, f"errors_{model_name}.csv", mesh_id_map)
    return f1, precision, recall


def evaluate_train_validation(model: Callable, model_name: str, x_train, y_train, x_val, y_val, mesh_id_map):
    training_f1, training_precision, training_recall = evaluate(
        model, f"train_{model_name}", x_train, y_train, mesh_id_map)
    validation_f1, validation_precision, validation_recall = evaluate(
        model, f"validation_{model_name}", x_val, y_val, mesh_id_map)
    print(f"=== {model_name} ===")
    print("Training F1 Score:", training_f1)
    print("Training Precision:", training_precision)
    print("Training Recall:", training_recall)
    print("-------")
    print("Validation F1 Score:", validation_f1)
    print("Validation Precision:", validation_precision)
    print("Validation Recall:", validation_recall)
    print("-------")


def parse_args():
    argument_parser = ArgumentParser(description="Evaluates NER-NEN pipelines")
    argument_parser.add_argument("--mesh_categories", nargs="+", default=[
                                 "A", "C04.588", "C04.557"], help="Restrict output of pipelines to specific MeSH categories")
    argument_parser.add_argument("--term_column", default="tissue_or_cell_type",
                                 help="Column from which to read terms to normalize")
    argument_parser.add_argument(
        "--true_column", default="synonym", help="Column from which to true synonyms")
    argument_parser.add_argument(
        "--export_invalid_synonyms", action="store_true", default=False, help="Write terms from input file that are not in the specified MeSH categories to a csv file")
    argument_parser.add_argument(
        "--input_prefix", default="", help="Prefix to attach to all inputs of the NER+NEN pipleines")
    argument_parser.add_argument(
        "file", help="Path to file with terms and synonyms")
    argument_parser.add_argument(
        "pipelines", nargs="+", help="Names of pipelines to evaluate")
    return argument_parser.parse_args()


if __name__ == "__main__":
    logging.disable(logging.WARN)

    args = parse_args()
    nlp = create_entity_linking_pipeline_with_ner()
    mesh_tree_number_map = build_mesh_lookup("desc2025.xml")

    print("=== PRE-RUN CHECKS ===")
    test_mesh_id_map = {key.strip().lower(): entry.id
                        for key, entry in mesh_tree_number_map.items()}

    def test_model(term): return term
    # In this context, the first list will be the predictions so they should
    # not always be the same as the ground-truth. This is an unusual test case.
    assert abs(evaluate(test_model, "test_model",
                        pd.Series(
                            ["yellow marrow", "heart", "brain", "heart"]),
                        pd.Series(["bone marrow", "heart", "bone", "heart"]),
                        test_mesh_id_map)[0] - 2/3) <= 0.01
    assert abs(evaluate(test_model, "test_model",
                        pd.Series(
                            ["yellow marrow", "heart", "UNPARSED", "heart"]),
                        pd.Series(["bone marrow", "heart", "bone", "heart"]),
                        test_mesh_id_map)[0] - 2/3) <= 0.01
    print("=== PRE-RUN CHECKS COMPLETE ===")

    mesh_tree_number_map = {key: value for key, value in mesh_tree_number_map.items(
    ) if is_term_in_one_of_categories(key, mesh_tree_number_map, args.mesh_categories)}
    mesh_id_map = {key.strip().lower(): entry.id
                   for key, entry in mesh_tree_number_map.items()}
    resources = StandardizationResources(mesh_tree_number_map, nlp)

    terms_synoyms_df = pd.read_csv(args.file)
    synonym_column = args.true_column
    term_column = args.term_column

    terms_synoyms_df = terms_synoyms_df[
        terms_synoyms_df[synonym_column] != "UNKNOWN"]
    invalid_synonyms = terms_synoyms_df[
        terms_synoyms_df[synonym_column].apply(lambda synonym: not is_synonym_valid(synonym, mesh_tree_number_map))]
    terms_synoyms_df = terms_synoyms_df[
        terms_synoyms_df[synonym_column].apply(lambda synonym: is_synonym_valid(synonym, mesh_tree_number_map))]

    x_full = terms_synoyms_df[term_column]
    y_full = terms_synoyms_df[synonym_column]

    x_full = x_full.apply(lambda term: f"{args.input_prefix}{term}")

    if "gilda_plus_spacy" in args.pipelines:
        def model(term): return get_standard_name(term, resources)
        evaluate(model, "gilda_plus_spacy", x_full,
                 y_full, mesh_id_map)

    if "spacy" in args.pipelines:
        def model(term): return get_standard_name_spacy(
            term, resources.nlp, resources.mesh_lookup)
        evaluate(
            model, "spacy", x_full, y_full, mesh_id_map)

    if "gilda" in args.pipelines:
        def model(term): return get_standard_name_gilda(
            term, resources.mesh_lookup)
        evaluate(
            model, "gilda", x_full, y_full, mesh_id_map)

    if "fasttext" in args.pipelines:
        fasttext_parser = FastTextParser(
            "BioWordVec_PubMed_MIMICIII_d200.vec.bin", mesh_tree_number_map)

        def model(term): return fasttext_parser.get_standard_name(term)[0]
        evaluate(model, "fasttext", x_full,
                 y_full, mesh_id_map)

    if "reranked_fasttext" in args.pipelines:
        def model(term): return fasttext_parser.get_standard_name_reranked(
            term)[0]
        evaluate(model, "reranked_fasttext", x_full,
                 y_full, mesh_id_map)

    if "gilda_plus_fasttext" in args.pipelines:
        def gilda_plus_fasttext(term):
            global mesh_tree_number_map
            term = term.replace("_", " ")
            gilda_name = get_standard_name_gilda(term, mesh_tree_number_map)
            if gilda_name:
                return gilda_name
            try:
                return fasttext_parser.get_standard_name_reranked(term)[0]
            except ValueError:
                return "UNPARSED"

        evaluate(gilda_plus_fasttext, "gilda_plus_fasttext",
                 x_full, y_full, mesh_id_map)

    if "bern2+ANGEL" in args.pipelines:
        bern2_ner = BERN2Recognizer()
        angel_normalizer = ANGELMeshNormalizer(mesh_tree_number_map)
        pipeline = NER_NEN_Pipeline(bern2_ner, angel_normalizer)

        def model(term): return pipeline(term)[
            0].standard_name if pipeline(term) else "UNPARSED"
        evaluate(model, "bern2+ANGEL", x_full,
                 y_full, mesh_id_map)

    if "bern2" in args.pipelines:
        mesh_term_to_id_map = {entry.id: key.strip().lower()
                               for key, entry in mesh_tree_number_map.items()}

        def model(term): return get_standard_name_bern2(
            term, mesh_term_to_id_map, mesh_tree_number_map,)
        evaluate(model, "bern2", x_full,
                 y_full, mesh_id_map)

    if "bern2+fasttext" in args.pipelines:
        bern2_ner = BERN2Recognizer()
        fasttext_normalizer = FasttextNormalizer(
            "BioWordVec_PubMed_MIMICIII_d200.vec.bin", mesh_tree_number_map)
        pipeline = NER_NEN_Pipeline(bern2_ner, fasttext_normalizer)

        def model(term): return pipeline(term)[
            0].standard_name if pipeline(term) else "UNPARSED"
        evaluate(model, "bern2+fasttext", x_full,
                 y_full, mesh_id_map)
