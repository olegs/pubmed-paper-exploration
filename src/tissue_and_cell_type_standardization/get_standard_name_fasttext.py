import numpy as np
from gensim.models import KeyedVectors
from nltk import download, word_tokenize
# Import and download stopwords from NLTK.
from nltk.corpus import stopwords
from scipy.spatial.distance import cosine
import numpy as np
from src.tissue_and_cell_type_standardization.entity_normalizer import EntityNormalizer, NormalizationResult

download('stopwords')  # Download stopwords list.
download('punkt_tab')
stop_words = stopwords.words('english')


def preprocess(sentence):
    return word_tokenize(sentence.strip().lower())


class FastTextParser:
    def __init__(self, fasttext_model_path, mesh_lookup, binary_model=True):
        self.model = KeyedVectors.load_word2vec_format(
            fasttext_model_path, binary=binary_model)
        self.model.fill_norms()
        self.mesh_embeddings = []
        for term, entry in mesh_lookup.items():
            self.mesh_embeddings.append(
                (entry.id, term, self.model.get_mean_vector(preprocess(term))))

    def _get_standard_name_cosine(self, name, top_k: int = 5):
        tokenized_name = preprocess(name)
        name_embedding = self.model.get_mean_vector(tokenized_name)
        term_similarities = []

        for id, mesh_term, mesh_embedding in self.mesh_embeddings:
            score = cosine(name_embedding, mesh_embedding)
            term_similarities.append((id, mesh_term, score))

        term_similarities = list(
            filter(lambda x: not np.isnan(x[2]), term_similarities))
        top_similarities = list(
            sorted(term_similarities, key=lambda x: x[2]))[:top_k]
        if len(top_similarities) == 0:
            raise ValueError("Could not embed term " + name)
        return top_similarities

    def get_standard_name(self, name, top_k: int = 5):
        return [sim[1] for sim in self._get_standard_name_cosine(name, top_k)]

    def get_standard_name_reranked(self, name, top_k: int = 50, n_output_terms=5):
        term_similarities = self._get_standard_name_cosine(name, top_k * 3)
        name = preprocess(name)
        top_synonyms = []
        seen_ids = set()

        for similarity in term_similarities:
            if top_k == 0:
                break
            if similarity[0] in seen_ids:
                continue
            seen_ids.add(similarity[0])
            top_synonyms.append((
                similarity[0],
                similarity[1],
                self.model.wmdistance(name, preprocess(similarity[1]))
            ))
            top_k -= 1

        # rerank
        top_synonyms = [
            synonym for synonym in top_synonyms if not np.isnan(synonym[2])]
        top_synonyms = list(sorted(top_synonyms, key=lambda x: x[2]))
        return [synonym_score[1] for synonym_score in top_synonyms[:n_output_terms]]


import time

class FasttextNormalizer(EntityNormalizer):
    def __init__(self, fasttext_model_path, mesh_lookup, binary_model=True):
        begin = time.time()
        self.model = KeyedVectors.load_word2vec_format(
            fasttext_model_path, binary=binary_model)
        self.model.fill_norms()
        end = time.time()
        print("Fasttext load time", end - begin)

        begin = time.time()
        self.mesh_embeddings = []
        for term, entry_or_id in mesh_lookup.items():
            term_id = entry_or_id.id if not isinstance(entry_or_id, str) else entry_or_id
            self.mesh_embeddings.append(
                (term_id, term, self.model.get_mean_vector(preprocess(term))))
        end = time.time()
        print(self.mesh_embeddings[0])


    def _get_standard_name_cosine(self, name, top_k: int = 5):
        tokenized_name = preprocess(name)
        name_embedding = self.model.get_mean_vector(tokenized_name)
        term_similarities = []

        for id, mesh_term, mesh_embedding in self.mesh_embeddings:
            score = cosine(name_embedding, mesh_embedding)
            term_similarities.append((id, mesh_term, score))

        term_similarities = list(
            filter(lambda x: not np.isnan(x[2]), term_similarities))
        top_similarities = list(
            sorted(term_similarities, key=lambda x: x[2]))[:top_k]
        if len(top_similarities) == 0:
            raise ValueError("Could not embed term " + name)
        return top_similarities

    def get_standard_name(self, name, top_k: int = 5):
        return [sim[1] for sim in self._get_standard_name_cosine(name, top_k)]
    
    def get_standard_name_with_score(self, name, top_k: int = 5):
        return [sim[1:3] for sim in self._get_standard_name_cosine(name, top_k)]


    def get_standard_name_reranked(self, name, top_k: int = 50, n_output_terms=5):
        term_similarities = self._get_standard_name_cosine(name, top_k * 3)
        name = preprocess(name)
        top_synonyms = []
        seen_ids = set()

        for similarity in term_similarities:
            if top_k == 0:
                break
            if similarity[0] in seen_ids:
                continue
            seen_ids.add(similarity[0])
            top_synonyms.append((
                similarity[0],
                similarity[1],
                self.model.wmdistance(name, preprocess(similarity[1]))
            ))
            top_k -= 1

        # rerank
        top_synonyms = [
            synonym for synonym in top_synonyms if not np.isnan(synonym[2])]
        top_synonyms = list(sorted(top_synonyms, key=lambda x: x[2]))
        return [synonym_score for synonym_score in top_synonyms[:n_output_terms]]

    def normalize_entity(self, entity):
        scores = self.get_standard_name_reranked(entity)
        result = []
        for score in scores:
            result.append(NormalizationResult(entity, score[1], "MeSH", score[0], score[2]))
        return result[0]

if __name__ == "__main__":
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    import time
    mesh_lookup = build_mesh_lookup("desc2025.xml")
    begin = time.time()
    normalizer = FasttextNormalizer("BioWordVec_PubMed_MIMICIII_d200.vec.bin", mesh_lookup)
    end = time.time()
    print("Parser ready in ", end-begin, "seconds")

    begin = time.time()
    result = normalizer("lymph node")
    print(result)
    end = time.time()
    print("Parsing done in ", end-begin, "seconds")

    while True:
        name = input("Enter name to standardize: ")
        top_k = int(input("Enter topk"))
        n_outputs = int(input("Enter nubmer of outputs: "))
        print("standardizing:", name)
        begin = time.time()
        print(normalizer(name))
        print(normalizer(name)[0:5])
        print(normalizer.get_standard_name_reranked(name, 50, n_outputs))
        print(normalizer.get_standard_name(name, n_outputs))
        end = time.time()
        print("Parsing done in ", end-begin, "seconds")
