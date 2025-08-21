from typing import List, Dict
import time
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.manifold import TSNE
from src.ingestion.download_geo_datasets import download_geo_datasets
from src.ingestion.download_samples import download_samples_for_datasets
from src.analysis.vectorize_datasets import vectorize_datasets
from src.analysis.cluster import auto_cluster, get_clusters_top_terms
from src.analysis.analysis_result import AnalysisResult
from src.config import logger
from src.model.geo_dataset import GEODataset
from src.tissue_and_cell_type_standardization.get_standard_name_bern2 import BERN2Error
from src.tissue_and_cell_type_standardization.bern2_angel_pipeline import BERN2AngelPipeline
from src.analysis.standardization_resources import StandardizationResources
from src.model.geo_sample import GEOSample
from src.analysis.get_term_hierarchy import get_hierarchy
import pandas as pd
from tqdm import tqdm


class DatasetAnalyzer:
    def __init__(self, svd_components, mesh_lookup, ncbi_gene):
        self.svd = make_pipeline(
            TruncatedSVD(n_components=svd_components, random_state=42),
            Normalizer(copy=False),
        )
        self.tsne = TSNE(n_components=2, random_state=42)
        self.characteristics_to_standardize = [
            ("disease", ["disease", "disease state"]),
            ("tissue", ["tissue"]),
            ("cell_type", ["cell type"]),
        ]
        self.mesh_lookup = mesh_lookup
        self.normalization_cache = {}
        if mesh_lookup:
            self.standardization_resources = StandardizationResources(
                mesh_lookup)
            self.bern2_pipeline = BERN2AngelPipeline(mesh_lookup, ncbi_gene, must_normalize_to_mesh=True)

    def analyze_paper_datasets(self, pubmed_ids: List[int]) -> AnalysisResult:
        """
        Analyzes the datasets that are associated with the given PubMed IDs and
        clusters them.

        :param pumbed_ids: List of PubMed IDs for which to analyze datasets.
        :return: An instance of AnalysisResult containg the results.
        """

        datasets = download_geo_datasets(pubmed_ids)
        samples = download_samples_for_datasets(datasets)
        return self.analyze_datasets(datasets, samples)

    def analyze_datasets(self, datasets: List[GEODataset], samples: List[GEOSample] | None=None):
        """
        Analyzes the datasets and clusters them.

        :param datasets: List of GEODataset objects.
        :return: An instance of AnalysisResult containg the results.
        """
        embeddings, vocabulary = vectorize_datasets(datasets)
        embeddings_svd = self.svd.fit_transform(embeddings)

        explained_variance = self.svd[0].explained_variance_ratio_.sum()
        logger.info("Explained variance of the SVD step: %.1f %%",
                    explained_variance * 100)

        begin = time.time()
        cluster_assignments, silhouette_score, n_clusters = auto_cluster(
            embeddings_svd)
        end = time.time()
        self.n_clusters = n_clusters
        logger.info("Clustering time: %.2fs", end - begin)
        cluster_topics = get_clusters_top_terms(
            embeddings, cluster_assignments, vocabulary
        )

        self.tsne.perplexity = min(30, len(datasets) - 1)
        tsne_embeddings_2d = self.tsne.fit_transform(embeddings_svd)
        unique_characteristics_values = pd.DataFrame(self.standardize_unique_characteristics_values(
            datasets)) if self.mesh_lookup else None

        return AnalysisResult(
            datasets, n_clusters, cluster_assignments, cluster_topics, tsne_embeddings_2d, silhouette_score, unique_characteristics_values, None
        )

    def standardize_unique_characteristics_values(self, datasets: List[GEODataset]) -> pd.DataFrame:
        """
        """
        entities_per_dataset = {
            "id": [],
            "entities": []
        }
        for dataset in tqdm(datasets):
            entities_per_dataset["id"].append(dataset.id)
            dataset_with_characteristics_str = dataset.get_str_with_sample_characteristics()
            entities = []
            try:
                entities = self.bern2_pipeline(dataset_with_characteristics_str)
            except BERN2Error as e:
                print("BERN 2 API failed for dataset:", dataset.id)
                print(dataset_with_characteristics_str)
                print(e)
                entities = []
            entities_per_dataset["entities"].append(entities)


        
        return self._pivot_by_entity(entities_per_dataset)

    def _pivot_by_entity(self, entities_per_dataset):
        entity_types = list({entity.entity_class for entity_list in entities_per_dataset["entities"] for entity in entity_list})
        for entity_type in entity_types:
            entities_per_dataset[f"{entity_type}"] = []
            entities_per_dataset[f"{entity_type}_standardized"] = []
            entities_per_dataset[f"{entity_type}_ontology"] = []
            entities_per_dataset[f"{entity_type}_hierarchy"] = []
        
        for entity_list in entities_per_dataset["entities"]:
            for entity_type in entity_types:
                mentions = list(filter(lambda e: e.entity_class == entity_type, entity_list))
                seen_standard_names = set()
                mentions = [mention for mention in mentions if mention.standard_name not in seen_standard_names and not seen_standard_names.add(mention.standard_name)]
                entities_per_dataset[f"{entity_type}"].append(
                    [mention.mention for mention in mentions]
                )
                entities_per_dataset[f"{entity_type}_standardized"].append(
                    [mention.standard_name for mention in mentions]
                )
                entities_per_dataset[f"{entity_type}_ontology"].append(
                    [mention.ontology for mention in mentions]
                )
                entities_per_dataset[f"{entity_type}_hierarchy"].append(
                    [get_hierarchy(mention.standard_name, self.standardization_resources) for mention in mentions]
                )
        
        del entities_per_dataset["entities"]

        
        return pd.DataFrame(entities_per_dataset)



    def normalize(self, characteristic: str, value: str):
        string_to_normalize = f"{characteristic}: {value}"
        cached_normalization = self.normalization_cache.get(
            string_to_normalize)
        if cached_normalization:
            return cached_normalization

        invalid_mentions = ["disease", "diseases",
                            "cell type", "tissue", "tissues" "cell", "cells", "healthy", "normal"]
        entities = self.normalizers[characteristic](string_to_normalize)
        entities = [
            entity for entity in entities if (entity.mention not in invalid_mentions) and (entity.standard_name not in invalid_mentions)]

        self.normalization_cache[string_to_normalize] = entities[0].standard_name if entities else None
        return self.normalization_cache[string_to_normalize]

    def get_unique_standardized_characteristics_values(self, dataset: GEODataset) -> Dict[str, str]:
        """
        Returns both the standardized and raw unique characteristics values
        for a dataset. Only the disease, tissue and cell type characteristics
        are supported.
        :param dataset: GEODataset for which to get unique values of characteristics.
        :return: A dictionary containing the standardized and raw unique values of characteristics.
        The dictionary has the following structure:
        {
            "disease": [raw_disease1, raw_disease2, ...]
            "cell type": [raw_cell_type1, raw_cell_type2, ...]
            "tissue": [raw_tissue1, raw_cell_type2, ...]
            "disease_standardized": [standardized_disease1, standardized_disease2, ...]
            "cell_type_standardized": [standardized_cell_type1, standardized_cell_type2, ...]
            "tissue_standardized": [standardized_tissue1, standardized_cell_type2, ...]
        }
        """
        result = {}
        for characteristic, keys in self.characteristics_to_standardize:
            characteristic_values = sum(
                (dataset.get_unique_values(key) for key in keys), start=[])
            unique_characteristic_values = list(set(characteristic_values))
            unique_normalized_characteristic_values = [
                self.normalize(characteristic, value) for value in unique_characteristic_values
            ]
            result[characteristic] = unique_characteristic_values
            result[f"{characteristic}_standardized"] = unique_normalized_characteristic_values

        return result

    def get_standardized_characeristics_values(self, sample: GEOSample):
        standardized_sample_dict = {}
        standardized_sample_dict["id"] = sample.accession
        standardized_sample_dict["dataset_id"] = sample.dataset_id
        for characteristic, keys in self.characteristics_to_standardize:
            first_key_in_characteristics = next(
                (key for key in keys if key in sample.characteristics), None)
            if first_key_in_characteristics is not None:
                characteristic_value = sample.characteristics[first_key_in_characteristics]
                standardized_sample_dict[characteristic] = characteristic_value
                standardized_sample_dict[f"{characteristic}_standardized"] = self.normalize(
                    characteristic, characteristic_value)
                standardized_sample_dict[f"{characteristic}_hierarchy"] = get_hierarchy(
                    standardized_sample_dict[f"{characteristic}_standardized"], self.standardization_resources)

        return standardized_sample_dict


if __name__ == "__main__":
    SVD_COMPONENTS = 15
    with open("ids.txt") as file:
        pubmed_ids = map(int, file)
        analyzer = DatasetAnalyzer(SVD_COMPONENTS, 10)
        result = analyzer.analyze_paper_datasets(pubmed_ids)
        print(result.df.head())
        print(result.cluster_topics)
