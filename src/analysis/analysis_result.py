from src.model.geo_dataset import GEODataset
from typing import List
import numpy as np
import pandas as pd

class AnalysisResult:
    def __init__(
        self,
        datasets: List[GEODataset],
        cluster_assignments: np.array,
        cluster_topics: List[List[str]],
        tsne_embeddings_2d: np.ndarray,
        silhouette_score: float,
        standardized_characteristics_values: pd.DataFrame
    ):
        self.df = pd.DataFrame(list(map(GEODataset.to_dict, datasets)))
        self.df = pd.merge(self.df, standardized_characteristics_values, on="id", how="left", suffixes=("",""), sort=False) if standardized_characteristics_values else self.df
        self.datasets_list = self.df.to_dict(orient="records") if standardized_characteristics_values else list(map(GEODataset.to_dict, datasets))
        self.df["cluster"] = cluster_assignments
        self.df["x"] = tsne_embeddings_2d[:, 0]
        self.df["y"] = tsne_embeddings_2d[:, 1]
        self.cluster_topics = cluster_topics
        self.silhouette_score = silhouette_score