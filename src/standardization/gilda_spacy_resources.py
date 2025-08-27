from typing import Dict, Set
import spacy

class GildaSpacyResources:
    """
    A container for the resources needed by the get_standard_name function.
    Instances of this class are hashable, allowing them to be used with lru_cache.
    """
    def __init__(self, mesh_lookup: Dict[str, Set[str]], nlp: spacy.language.Language):
        self.mesh_lookup = mesh_lookup
        self.nlp = nlp

    def __hash__(self):
        return 1

    def __eq__(self, other):
        return isinstance(other, GildaSpacyResources)