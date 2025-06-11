from typing import List
import spacy
import scispacy.linking_utils
from scispacy.linking import EntityLinker
import gilda

def create_entity_linking_pipeline_with_ner(knowledge_base="umls"):
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
    nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": knowledge_base})
    return nlp


def link_entities(nlp, document: str) -> List[scispacy.linking_utils.Entity]:
    """
    Links entities in the document to the knowledge base of the scicpacy pipeline 
    and returns the canonical names and match scores.

    :param nlp: Scispacy NLP pipeline for entity linking and named entity
    recognition (see create_entity_linking_pipeline).
    :param document: The document in which to link entities to UMLS.
    :returns: A list of tuples (entity, canonical_name, score, label) where:
        1. entity is the name of the entity as it appears in the text.
        2. canonical_name is the canonical name of the entity in the knowledge base.
        3. score is the score of the knowledge base match. 
        4. NER label of the entity (e.g. ORGANISM, CELL, ...) 
        If an entity does not exist in the knowledge base it will be returned as (entity, entity, -1, None).
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
        entity_link = (ent, canonical_name, score, ent.label_)
        all_links.append(entity_link)
            
    return all_links

def get_entites(nlp, text):
    processed_doc = nlp(text)
    return [(ent, ent.label_) for ent in processed_doc.ents]


def get_standard_name_spacy(nlp, tissue: str):
    """
    Gets a common name for a specific tissue name.

    :param nlp: Scispacy NER and entity linking pipeline created by
    create_entity_linking_pipline_with_ner.
    :param tissue: The name of the tissue.
    :return: Tuple (tissue, common name, match score)
    """
    entity_links = link_entities(nlp, tissue)
    if not entity_links:
        return None

    relevant_labels = ["CELL", "TISSUE", "ORGAN", "ORGANISM_SUBSTANCE", "PATHOLOGICAL_FORMATION"]
    relevant_links = list(filter(lambda link: link[3] in relevant_labels, entity_links))
    if relevant_links:
        return max(relevant_links, key=lambda link: link[2])[1] # Return link with the highest score
    return max(entity_links, key=lambda link: link[2])[1]


if __name__ == "__main__":
    nlp = create_entity_linking_pipeline_with_ner("mesh")
    print(get_standard_name_spacy(nlp, "mouse fat"))
    print(get_standard_name_spacy(nlp, "whole body of single-housed females at 9 dph"))
    print(get_standard_name_spacy(nlp, "normal lung tissue"))
    print(get_standard_name_spacy(nlp, "penumbras tissue of brains"))
    print(get_standard_name_spacy(nlp, "left rectus abdominus"))
    print(get_standard_name_spacy(nlp, "gut"))
    print(get_standard_name_spacy(nlp, "trachea"))

    