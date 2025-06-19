from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import is_mesh_term_in_anatomy_or_cancer
from gensim.models import KeyedVectors
from gensim.models.fasttext import load_facebook_model
from nltk import download, word_tokenize
# Import and download stopwords from NLTK.
from nltk.corpus import stopwords

download('stopwords')  # Download stopwords list.
download('punkt_tab')
stop_words = stopwords.words('english')
import numpy as np


def preprocess(sentence):
    return word_tokenize(sentence.strip().lower())


def get_standard_name_fasttext(term, fasttext_model, mesh_lookup):
    term = preprocess(term)
    similiarties = [
        (
        mesh_term,
        fasttext_model.wmdistance(term, preprocess(mesh_term)) 
        ) for mesh_term in mesh_lookup
    ]
    top_5_synonym_scores = list(sorted(similiarties, key=lambda x: x[1]))[0:5]
    return [synonym_score[0] for synonym_score in top_5_synonym_scores]

if __name__ == "__main__":
    from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
    model = KeyedVectors.load_word2vec_format("BioWordVec_PubMed_MIMICIII_d200.vec.bin", binary=True)
    model.fill_norms() 
    mesh_lookup =  build_mesh_lookup("desc2025.xml")
    print(get_standard_name_fasttext("cd 8 positive t lymphocytes", model, mesh_lookup))