import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import spmatrix
from typing import List, Tuple
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError
from src.model.geo_dataset import GEODataset


def vectorize_datasets(datasets: List[GEODataset]) -> Tuple[spmatrix, List[str]]:
    """
    Constructs vector representations of datasets using tf-idf.
    The concatenation of the Title, Experiment type, Summary, Organism,
    and Overall design fields is used as the basis for the vectorization.

    :param datasets: Datasets to vectorize.
    :return: Tuple (Sparse matrix containing the tf-idf vectors of the datasets, Vocabulary of the datasets).
    """
    vectorizer = TfidfVectorizer(stop_words="english", max_df=0.5)
    corpus = map(str, datasets)
    try:
        dataset_embeddings = vectorizer.fit_transform(corpus)
    except ValueError:
        raise NotEnoughDatasetsError("Too few datasets to perform tf-idf vectorization")
    return dataset_embeddings, vectorizer.get_feature_names_out()

if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_datasets
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    datasets = download_geo_datasets(
        [30530648, 31820734, 31018141, 38539015, 33763704, 32572264]
    )
    embeddings = vectorize_datasets(datasets)
    print(f"n_datasets: {embeddings.shape[0]} n_features: {embeddings.shape[1]}")
    pairwise_similarities = cosine_similarity(embeddings)
    similarties_between_different_datasets = pairwise_similarities[~np.eye(similarities.shape[0],dtype=bool)].flatten()
    print(f"Min similarity: {min(similarties_between_different_datasets)}")
    print(f"Max similarity: {max(similarties_between_different_datasets)}")
    print(f"Mean similarity: {np.mean(similarties_between_different_datasets)}")
