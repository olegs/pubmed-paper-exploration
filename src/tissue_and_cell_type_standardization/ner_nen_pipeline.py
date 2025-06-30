from src.tissue_and_cell_type_standardization.named_entity_recognizer import NamedEntityRecognizer
from src.tissue_and_cell_type_standardization.entity_normalizer import EntityNormalizer
from collections import namedtuple
from typing import List

PipelineResult = namedtuple("PipelineResult", ["mention", "entity_class", "standard_name", "ontology", "cui", "score"])

class NER_NEN_Pipeline():
    def __init__(self, recognizer: NamedEntityRecognizer, normalizer: EntityNormalizer):
        self.recognizer = recognizer
        self.normalizer = normalizer

    def __call__(self, text: str) -> List[PipelineResult]:
        """
        Recognizes named entities in a piece of text and normalizes them.
        :param text: The text for which to normalize and standardize entities.
        :return: List of extracted and normalized entities.
        """
        entities = self.recognizer(text)
        normalized_enities = [self.normalizer(e.entity) for e in entities]
        result = []
        for i in range(len(entities)):
            mention = entities[i].entity
            entity_class = entities[i].entity_class
            standard_name = normalized_enities[i].standard_name if normalized_enities[i] else None
            cui = normalized_enities[i].cui if normalized_enities[i] else None
            ontology = normalized_enities[i].ontology if normalized_enities[i] else None
            score = normalized_enities[i].score if normalized_enities[i] else -1

            result.append(
                PipelineResult(mention, entity_class, standard_name, cui, ontology, score)
            )

        return result
