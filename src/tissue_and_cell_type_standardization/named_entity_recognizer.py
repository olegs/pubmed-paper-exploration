from typing import Tuple, List
from collections import namedtuple
from abc import ABC, abstractmethod

NamedEntity = namedtuple("NamedEntity", ["entity", "entity_class", "score"])

class NamedEntityRecognizer(ABC):
    @abstractmethod
    def extract_named_entities(self, text: str) -> List[NamedEntity]:
        """
        Performs NER on the text.

        :param text: The text on which to perform named entity recognition
        :return: List of NamedEntity objects containing the extracted named entities.
        """
    
    def __call__(self, text: str) -> List[NamedEntity]:
        return self.extract_named_entities(text)

