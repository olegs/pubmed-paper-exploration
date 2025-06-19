from typing import List, Dict, Set
import spacy
import scispacy.linking_utils
from scispacy.linking import EntityLinker
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import is_mesh_term_in_anatomy_or_cancer


def create_entity_linking_pipeline_with_ner(knowledge_base: str = "mesh") -> spacy.language.Language:
    """
    Returns a scispacy NLP pipeline for entity linking with the MeSH database
    that also performs named entity recognition.
    """
    nlp = spacy.load("en_ner_bionlp13cg_md")

    # This line takes a while, because we have to download ~1GB of data
    # and load a large JSON file (the knowledge base). Be patient!
    # Thankfully it should be faster after the first time you use it, because
    # the downloads are cached.
    # NOTE: The resolve_abbreviations parameter is optional, and requires that
    # the AbbreviationDetector pipe has already been added to the pipeline. Adding
    # the AbbreviationDetector pipe and setting resolve_abbreviations to True means
    # that linking will only be performed on the long form of abbreviations.
    nlp.add_pipe("scispacy_linker", config={
                 "resolve_abbreviations": True, "linker_name": knowledge_base})
    return nlp


class NEREntity():
    def __init__(self, term, canonical_name, score, ner_type):
        self.term = term
        self.cannonical_name = canonical_name
        self.score = score
        self.ner_type = ner_type


def link_entities(nlp, document: str, mesh_lookup: Dict[str, Set[str]]) -> List[NEREntity]:
    """
    Links entities in the document to the knowledge base of the scicpacy pipeline 
    and returns the canonical names and match scores.

    :param nlp: Scispacy NLP pipeline for entity linking and named entity
    recognition (see create_entity_linking_pipeline).
    :param document: The document in which to link entities to UMLS.
    :param mesh_lookup: A pre-built dictionary mapping MeSH terms to tree 
        numbers (see build_mesh_lookup).
    :returns: A list of NEREntity objects representing entities that were found
    in the document.
    """
    processed_doc = nlp(document)
    linker = nlp.get_pipe("scispacy_linker")
    knowledge_base = linker.kb
    all_links = []
    for ent in processed_doc.ents:
        if not ent._.kb_ents:
            all_links.append(NEREntity(ent, ent, -1, ent.label_))
            continue

        concept_id, score = ent._.kb_ents[0]
        umls_entity = knowledge_base.cui_to_entity[concept_id]
        canonical_name = umls_entity.canonical_name
        entity_link = NEREntity(ent, canonical_name, score, ent.label_)
        if is_mesh_term_in_anatomy_or_cancer(canonical_name, mesh_lookup):
            all_links.append(entity_link)

    return all_links


def get_standard_name_spacy(name: str, nlp, mesh_lookup: Dict[str, Set[str]]) -> str:
    """
    Gets the standard name for a tissue or cell type using the scipacy's 
    NER and entity linking features.

    :param name: Tissue or cell type name to standardize.
    :param nlp: Scispacy NER and entity linking pipeline created by
    create_entity_linking_pipline_with_ner.
    :param mesh_lookup: A pre-built dictionary mapping MeSH terms to tree 
        numbers (see build_mesh_lookup).

    :return: Standardized name of the tissue or cell type or the input name if
    the standardized name cannot be determined.
    """
    linked_entities = link_entities(nlp, name, mesh_lookup)
    if not linked_entities:
        return name

    standardized_entity = max(
        linked_entities, key=lambda linked_entity: linked_entity.score).cannonical_name
    return standardized_entity if isinstance(standardized_entity, str) else standardized_entity.text


if __name__ == "__main__":
    nlp = create_entity_linking_pipeline_with_ner("mesh")
    print(get_standard_name_spacy(nlp, "mouse fat"))
    print(get_standard_name_spacy(
        nlp, "whole body of single-housed females at 9 dph"))
    print(get_standard_name_spacy(nlp, "normal lung tissue"))
    print(get_standard_name_spacy(nlp, "penumbras tissue of brains"))
    print(get_standard_name_spacy(nlp, "left rectus abdominus"))
    print(get_standard_name_spacy(nlp, "gut"))
    print(get_standard_name_spacy(nlp, "trachea"))
