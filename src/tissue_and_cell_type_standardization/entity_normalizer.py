from collections import namedtuple
from abc import ABC, abstractmethod

NormalizationResult = namedtuple('NormalizationResult', ["mention", "standard_name", "ontology", "cui", "score"])

class EntityNormalizer(ABC):
    @abstractmethod
    def normalize_entity(self, entity:str) -> NormalizationResult | None:
        """
        Normalizes a mention of a concept to a standard name in an ontology.
        :param entity: The entity to normalize.
        :return: NormalizationResult object containing the standard name or None
          if the entity was not able to be normalized.
        """
    
    def __call__(self, text: str):
        return self.normalize_entity(text)

