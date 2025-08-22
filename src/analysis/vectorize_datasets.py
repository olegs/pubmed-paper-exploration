import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import spmatrix
from typing import List, Tuple
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError
from src.model.geo_dataset import GEODataset
from src.analysis.text import vectorize_corpus, embeddings, chunks_to_text_embeddings
from src.config.config import VECTOR_WORDS, VECTOR_MIN_DF, VECTOR_MAX_DF
import pandas as pd


def vectorize_datasets(datasets: List[GEODataset]) -> Tuple[spmatrix, List[str]]:
    """
    Constructs vector representations of datasets using tf-idf.
    The concatenation of the Title, Experiment type, Summary, Organism,
    and Overall design fields is used as the basis for the vectorization.

    :param datasets: Datasets to vectorize.
    :return: Tuple (Sparse matrix containing the tf-idf vectors of the datasets, Vocabulary of the datasets).
    """
    df = pd.DataFrame(
        {
            "id": dataset.id,
            "title": dataset.title,
            "abstract": dataset.get_metadata_str()
        }
    for dataset in datasets)
    corpus, corpus_tokens, corpus_counts = vectorize_corpus(
        df, max_features=VECTOR_WORDS, min_df=VECTOR_MIN_DF, max_df=VECTOR_MAX_DF, test=False
    )

    chunks_embeddings, chunks_idx = embeddings(
        df, corpus, corpus_tokens, corpus_counts, test=False
    )
    return chunks_to_text_embeddings(df, chunks_embeddings, chunks_idx), corpus_tokens, corpus_counts

if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_datasets
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    datasets = download_geo_datasets(
        [30530648, 31820734, 31018141, 38539015, 33763704, 32572264]
    )
    embeddings, _ = vectorize_datasets(datasets)
    print(f"n_datasets: {embeddings.shape[0]} n_features: {embeddings.shape[1]}")
    pairwise_similarities = cosine_similarity(embeddings)
    similarties_between_different_datasets = pairwise_similarities[~np.eye(similarities.shape[0],dtype=bool)].flatten()
    print(f"Min similarity: {min(similarties_between_different_datasets)}")
    print(f"Max similarity: {max(similarties_between_different_datasets)}")
    print(f"Mean similarity: {np.mean(similarties_between_different_datasets)}")
