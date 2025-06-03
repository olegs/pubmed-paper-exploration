from typing import List
import time
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.manifold import TSNE
from src.ingestion.download_geo_datasets import download_geo_datasets
from src.analysis.vectorize_datasets import vectorize_datasets
from src.analysis.cluster import cluster, get_clusters_top_terms
from src.analysis.analysis_result import AnalysisResult
from src.config import logger
from src.model.geo_dataset import GEODataset


class DatasetAnalyzer:
    def __init__(self, svd_components, n_clusters):
        self.svd = make_pipeline(
            TruncatedSVD(n_components=svd_components, random_state=42),
            Normalizer(copy=False),
        )
        self.tsne = TSNE(n_components=2, random_state=42)
        self.n_clusters = n_clusters

    def analyze_paper_datasets(self, pubmed_ids: List[int]) -> AnalysisResult:
        """
        Analyzes the datasets that are associated with the given PubMed IDs and
        clusters them.

        :param pumbed_ids: List of PubMed IDs for which to analyze datasets.
        :return: An instance of AnalysisResult containg the results.
        """

        datasets = download_geo_datasets(pubmed_ids)
        return self.analyze_datasets(datasets)
    
    def analyze_datasets(self, datasets: List[GEODataset]):
        """
        Analyzes the datasets and clusters them.

        :param datasets: List of GEODataset objects.
        :return: An instance of AnalysisResult containg the results.
        """
        embeddings, vocabulary = vectorize_datasets(datasets)
        embeddings_svd = self.svd.fit_transform(embeddings)

        explained_variance = self.svd[0].explained_variance_ratio_.sum()
        logger.info("Explained variance of the SVD step: %.1f %%", explained_variance * 100)

        begin = time.time()
        cluster_assignments, silhouette_score = cluster(embeddings_svd, self.n_clusters)
        end = time.time()
        logger.info("Clustering time: %.2fs", end - begin)
        cluster_topics = get_clusters_top_terms(
            embeddings, cluster_assignments, vocabulary
        )

        self.tsne.perplexity = min(30, len(datasets) - 1)
        tsne_embeddings_2d = self.tsne.fit_transform(embeddings_svd)

        return AnalysisResult(
            datasets, cluster_assignments, cluster_topics, tsne_embeddings_2d, silhouette_score
        )


if __name__ == "__main__":
    SVD_COMPONENTS = 15
    with open("ids.txt") as file:
        pubmed_ids = map(int, file)
        analyzer = DatasetAnalyzer(SVD_COMPONENTS, 10)
        result = analyzer.analyze_paper_datasets(pubmed_ids)
        print(result.df.head())
        print(result.cluster_topics)
