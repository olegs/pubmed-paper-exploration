from src.analysis.analysis_result import AnalysisResult
from src.analysis.analyzer import DatasetAnalyzer
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError
import pytest

SVD_COMPONENTS = 15
NUMBER_OF_CLUSTERS = 10


def assert_valid_result(analysis_result: AnalysisResult, number_of_clusters: int):
    required_columns = [
        "x",
        "y",
        "cluster",
        "id",
        "title",
        "summary",
        "organisms",
        "experiment_type",
        "overall_design",
    ]
    assert len(analysis_result.cluster_topics) == number_of_clusters
    assert all(len(topic) > 0 for topic in analysis_result.cluster_topics)
    assert all(col in analysis_result.df for col in required_columns)
    assert all(
        0 <= topic_label < number_of_clusters
        for topic_label in analysis_result.df["cluster"]
    )


@pytest.mark.parametrize(
    "pubmed_ids",
    [[30530648, 31820734, 31018141, 38539015, 32572264, 31002671, 33309739, 21057496]],
)
def test_analyzer_produces_valid_result(pubmed_ids):
    with open("ids.txt") as file:
        pubmed_ids = map(int, file)
        analyzer = DatasetAnalyzer(SVD_COMPONENTS, NUMBER_OF_CLUSTERS)
        result = analyzer.analyze_paper_datasets(pubmed_ids)
        assert_valid_result(result, NUMBER_OF_CLUSTERS)


@pytest.mark.parametrize(
    "pubmed_ids", [([30530648, 31820734]), ([30530648, 31820734, 31018141, 38539015])]
)
def test_analyzer_raises_error_when_there_are_not_enough_datasets(pubmed_ids):
    analyzer = DatasetAnalyzer(SVD_COMPONENTS, NUMBER_OF_CLUSTERS)
    with pytest.raises(NotEnoughDatasetsError):
        result = analyzer.analyze_paper_datasets(pubmed_ids)
