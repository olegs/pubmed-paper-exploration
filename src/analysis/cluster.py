from typing import List, Tuple

import numpy as np
from scipy.sparse import spmatrix
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

from src.config import config, logger
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError

n_topic_words = config.topic_words


def get_clusters_top_terms(
        cluster_assignments: List[int], vocabulary, corpus_counts, n_topic_words,
) -> List[List[str]]:
    """
    Identifies key descriptive words for each cluster by analyzing the
    frequencies of words in dataset descriptions. Words are ranked
    based on how closely their frequencies in each cluster match a
    reference pattern where each word is strongly associated with a single
    cluster ([0, ..., 0, 1, 0, ..., 0] vector). This similiraty is measured
    using cosine_similarity.

    Based on _get_topics_description_cosine from PubTrends.

    :param cluster_assignements: Cluster assignments for each dataset.
    :param vocabulary: Vocabulary of the datasets.
    :param corpus_counts: Number of occurences of each token in each dataset.
    :param n_topic_words: Number of key words to extract for each cluster.
    :return: List of lists of most influential terms for every cluster.
    """

    n_clusters = np.max(cluster_assignments) + 1
    tokens_freqs_per_comp = np.zeros(
        shape=(n_clusters, corpus_counts.shape[1]), dtype=np.float32)
    for cluster_idx in range(n_clusters):
        tokens_freqs_per_comp[cluster_idx] = np.sum(
            corpus_counts[cluster_assignments == cluster_idx], axis=0
        )

    # Calculate total number of occurrences for each word
    tokens_freqs_total = np.sum(tokens_freqs_per_comp, axis=0)

    # Normalize frequency vector for each word to have length of 1
    tokens_freqs_norm = np.sqrt(
        np.diag(tokens_freqs_per_comp.T @ tokens_freqs_per_comp))
    tokens_freqs_per_comp = tokens_freqs_per_comp / tokens_freqs_norm

    logger.debug(
        'Take frequent tokens that have the most descriptive frequency vector for topics')
    # Calculate cosine distance between the frequency vector and [0, ..., 0, 1, 0, ..., 0] for each cluster
    cluster_mask = np.eye(n_clusters)
    distance = tokens_freqs_per_comp.T @ cluster_mask
    # Add some weight for more frequent tokens to get rid of extremely rare ones in the top
    adjusted_distance = distance.T * np.log1p(tokens_freqs_total)

    top_term_indices_per_cluster = adjusted_distance.argsort()[:, ::-1]
    top_terms = []
    for cluster_idx in range(n_clusters):
        top_terms.append([])
        for ind in top_term_indices_per_cluster[cluster_idx, :n_topic_words]:
            top_terms[-1].append(vocabulary[ind])

    return top_terms


def sort_cluster_labels(cluster_assignments: np.array) -> np.array:
    """
    Relabels the clusters based on their size.
    :param cluster_assignments: Unordered cluster assignements.
    :return: Cluster assignements where the cluster labels are ordered by the size of the clusters.
    """
    cluster_labels, counts = np.unique(cluster_assignments, return_counts=True)
    cluster_labels_sorted = cluster_labels[np.argsort(-counts)]
    cluster_ranks = {cluster_label: rank for rank,
    cluster_label in enumerate(cluster_labels_sorted)}
    return np.array([cluster_ranks[cluster_assignment] for cluster_assignment in cluster_assignments])


def cluster(embeddings: spmatrix, n_clusters: int) -> Tuple[List[int], np.ndarray]:
    """
    Clusters the vector representations of GEO datasets.

    :param embeddings: Vector representations of the datasets.
    :param n_cluster: Number of clusters to create.
    :return: Cluster assignements for each dataset and silhouette score.
    """

    clusterer = KMeans(n_clusters=n_clusters, random_state=42)

    try:
        cluster_assignments = clusterer.fit_predict(embeddings)
    except ValueError:
        raise NotEnoughDatasetsError(
            f"Cannot extract {n_clusters} clusters for {embeddings.shape[0]} datasets"
        )
    cluster_assignments = sort_cluster_labels(cluster_assignments)

    silhouette_avg = silhouette_score(embeddings, cluster_assignments)
    logger.debug(f"Silhouette score: {silhouette_avg}")

    return cluster_assignments, silhouette_avg


def auto_cluster(embeddings: spmatrix) -> Tuple[List[int], np.ndarray]:
    """
    Clusters the vector representations of GEO datasets and chooses the optimal
    number of clusters based on silhoutte score.

    :param embeddings: Vector representations of the datasets.
    :return: Cluster assignements for each dataset, silhouette score and number of clusters.
    """
    best_clustering = (None, -1, 0)
    for n_cluster in range(2, min(20, embeddings.shape[0])):
        cluster_assignments, silhouette_score = cluster(embeddings, n_cluster)
        if silhouette_score > best_clustering[1]:
            best_clustering = (cluster_assignments,
                               silhouette_score, n_cluster)

    return best_clustering


if __name__ == "__main__":
    from src.ingestion.download_geo_datasets import download_geo_datasets
    from src.analysis.vectorize_datasets import vectorize_datasets
    import time

    SVD_COMPONENTS = 15
    N_CLUSTERS = 10

    # ids.txt is a copy of the provided PMIDs_list.txt
    with open("ids.txt") as file:
        pubmed_ids = list(map(int, file))
        datasets = download_geo_datasets(pubmed_ids)

        embeddings, vocabulary = vectorize_datasets(datasets)
        lsa = make_pipeline(
            TruncatedSVD(n_components=SVD_COMPONENTS, random_state=42),
            Normalizer(copy=False),
        )
        embeddings_svd = lsa.fit_transform(embeddings)
        explained_variance = lsa[0].explained_variance_ratio_.sum()
        print(
            f"Explained variance of the SVD step: {explained_variance * 100:.1f}%")

        begin = time.time()
        labels, score, n_clusters = auto_cluster(embeddings_svd)
        end = time.time()
        print("Clustering time:", end - begin)
        print("Number of clusters", n_clusters)
        print("Silhouette score", score)
        topics = get_clusters_top_terms(embeddings, labels, vocabulary)
        for i in range(len(topics)):
            print(f"Cluster {i} topics: {' '.join(topics[i])}")
