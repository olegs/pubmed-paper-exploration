from src.tissue_and_cell_type_standardization.named_entity_recognizer import NamedEntityRecognizer, NamedEntity
from gliner import GLiNER


class GlinerRecognizer(NamedEntityRecognizer):
    def __init__(self, labels=["Disease", "Drug", "Drug dosage", "Drug frequency", "Lab test", "Lab test value", "Demographic information"]
                 ):
        self.model = GLiNER.from_pretrained("Ihor/gliner-biomed-large-v1.0")

        self.labels = labels

    def extract_named_entities(self, text: str):
        entities = self.model.predict_entities(
            text, self.labels, threshold=0.5)
        results = []

        for entity in entities:
            print(entity)
            print(entity["text"], "=>", entity["label"])
            results.append(NamedEntity(entity["text"], entity["label"], entity["score"]))

        return results


if __name__ == "__main__":
    recognizer = GlinerRecognizer(["Tissue", "Cell Type", "Age", "Healthy or Disease", "Cell Line", "Gender"])

    while True:
        text = input(">")
        print(recognizer(text))
