from src.model.geo_dataset import GEODataset
from src.model.geo_sample import GEOSample
from src.analysis.get_term_hierarchy import get_hierarchy_for_experiment_type
from typing import List, Dict
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
        standardized_characteristics_values: pd.DataFrame,
        standardized_samples: pd.DataFrame | None = None,
    ):
        self.df: pd.DataFrame = pd.DataFrame(list(map(GEODataset.to_dict, datasets)))
        self.df["experiment_type_hierarchy"] = self.df["experiment_type"].map(lambda et: [get_hierarchy_for_experiment_type(et)])
        self.df = pd.merge(self.df, standardized_characteristics_values, on="id", how="left", suffixes=("",""), sort=False) if standardized_characteristics_values is not None else self.df
        self.datasets_list = self.df.to_dict(orient="records") if standardized_characteristics_values is not None else list(map(GEODataset.to_dict, datasets))
        self.df["cluster"] = cluster_assignments
        self.df["x"] = tsne_embeddings_2d[:, 0]
        self.df["y"] = tsne_embeddings_2d[:, 1]
        self.cluster_topics: List = cluster_topics
        self.silhouette_score: float = silhouette_score
        self.samples: pd.DataFrame | None = standardized_samples