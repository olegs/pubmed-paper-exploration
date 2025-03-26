from src.ingestion.download_geo_datasets import download_geo_datasets
from src.analysis.vectorize_datasets import vectorize_datasets
from src.analysis.cluster import cluster, get_clusters_top_terms
from src.model.geo_dataset import GEODataset
from typing import List
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.manifold import TSNE
import pandas as pd
import time

SVD_COMPONENTS = 15


class AnalysisReusult:
    def __init__(
        self,
        datasets: List[GEODataset],
        cluster_assignments: np.array,
        cluster_topics: List[List[str]],
        tsne_embeddings_2d: np.ndarray,
    ):
        self.df = pd.DataFrame(map(GEODataset.to_dict, datasets))
        self.df["cluster"] = cluster_assignments
        self.df["x"] = tsne_embeddings_2d[:, 0]
        self.df["y"] = tsne_embeddings_2d[:, 1]
        self.cluster_topics = cluster_topics


class DatasetAnalyzer:
    def __init__(self, svd_components, n_clusters):
        self.svd = make_pipeline(
            TruncatedSVD(n_components=svd_components, random_state=42),
            Normalizer(copy=False),
        )
        self.tsne = TSNE(n_components=2, random_state=42)
        self.n_clusters = n_clusters

    def analyze_datasets(self, pubmed_ids: List[str]) -> AnalysisReusult:
        """
        Analyzes the datasets that are associated with the given PubMed IDs and
        clusters them.

        :param pumbed_ids: List of PubMed IDs for which to analyze datasets.
        :return: An instance of AnalysisResult containg the results.
        """

        datasets = download_geo_datasets(pubmed_ids)
        embeddings, vocabulary = vectorize_datasets(datasets)
        embeddings_svd = self.svd.fit_transform(embeddings)

        explained_variance = self.svd[0].explained_variance_ratio_.sum()
        print(f"Explained variance of the SVD step: {explained_variance * 100:.1f}%")

        begin = time.time()
        cluster_assignments = cluster(embeddings_svd, self.n_clusters)
        end = time.time()
        print("Clustering time:", end - begin)
        cluster_topics = get_clusters_top_terms(embeddings, cluster_assignments, vocabulary)
        tsne_embeddings_2d = self.tsne.fit_transform(embeddings_svd)

        return AnalysisReusult(
            datasets, cluster_assignments, cluster_topics, tsne_embeddings_2d
        )


if __name__ == "__main__":
    with open("ids.txt") as file:
        pubmed_ids = map(int, file)
        analyzer = DatasetAnalyzer(SVD_COMPONENTS, 10)
        result = analyzer.analyze_datasets(pubmed_ids)
        print(result.df.head())
        print(result.cluster_topics)
