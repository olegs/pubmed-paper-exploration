from typing import List, Tuple
import spacy
import scispacy.linking_utils
from scispacy.linking import EntityLinker


def create_entity_linking_pipeline_with_ner(knowledge_base: str = "umls") -> spacy.language.Language:
    """
    Returns a scispacy NLP pipeline for entity linking with the UMLS database
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


def link_entities(nlp, document: str) -> List[NEREntity]:
    """
    Links entities in the document to the knowledge base of the scicpacy pipeline 
    and returns the canonical names and match scores.

    :param nlp: Scispacy NLP pipeline for entity linking and named entity
    recognition (see create_entity_linking_pipeline).
    :param document: The document in which to link entities to UMLS.
    :returns: A list of NEREntity objects representing entities that were found
    in the document.
    """
    processed_doc = nlp(document)
    linker = nlp.get_pipe("scispacy_linker")
    knowledge_base = linker.kb
    all_links = []
    for ent in processed_doc.ents:
        if not ent._.kb_ents:
            all_links.append((ent, ent, -1, ent.label_))
            continue

        concept_id, score = ent._.kb_ents[0]
        umls_entity = knowledge_base.cui_to_entity[concept_id]
        canonical_name = umls_entity.canonical_name
        entity_link = NEREntity(ent, canonical_name, score, ent.label_)
        all_links.append(entity_link)

    return all_links


def get_standard_name_spacy(name: str, nlp) -> str:
    """
    Gets the standard name for a tissue or cell type using the scipacy's 
    NER and entity linking features.

    Uses the UMLS database to perform entity linking.

    :param name: Tissue or cell type name to standardize.
    :param nlp: Scispacy NER and entity linking pipeline created by
    create_entity_linking_pipline_with_ner.

    :return: Standardized name of the tissue or cell type or the input name if
    the standardized name cannot be determined.
    """
    linked_entities = link_entities(nlp, name)
    if not linked_entities:
        return None

    # Prefer entity types that are more likely to be valid tissue or cell type names
    relevant_entity_types = ["CELL", "TISSUE", "ORGAN",
                             "ORGANISM_SUBSTANCE", "PATHOLOGICAL_FORMATION"]
    relevant_entities = list(
        filter(lambda linked_entity: linked_entity.ner_type in relevant_entity_types, linked_entities))
    if relevant_entities:
        # Return link with the highest score
        return max(relevant_entities, key=lambda linked_entity: linked_entity.score).cannonical_name
    return max(linked_entities, key=lambda linked_entity: linked_entity.score).cannonical_name


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
