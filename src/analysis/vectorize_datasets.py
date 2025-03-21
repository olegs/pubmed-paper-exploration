import sys

from typing import List
from src.model.geo_dataset import GEODataset
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import spmatrix

def vectorize_datasets(datasets: List[GEODataset]) -> spmatrix:
    """
    Constructs vector representations of datasets using tf-idf.
    The concatenation of the Title, Experiment type, Summary, Organism,
    and Overall design fields is used as the basis for the vectorization.

    :param datasets: Datasets to vectorize.
    :return: Sparse matrix containing the tf-idf vectors of the datasets.
    """
    vectorizer = TfidfVectorizer(stop_words="english", max_df=0.5)
    corpus = map(str, datasets)
    dataset_embeddings = vectorizer.fit_transform(corpus)
    return dataset_embeddings


if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_datasets

    datasets = download_geo_datasets([30530648,31820734,31018141,38539015,33763704,32572264])
    embeddings = vectorize_datasets(datasets)
    print(embeddings)
