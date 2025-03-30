from typing import List, Tuple
import pandas as pd
from src.visualization.visualize_clusters import get_topic_colors

def get_topic_table(
    cluster_topics: List[List[str]], datasets_df: pd.DataFrame
) -> List[Tuple[int, int, str, str]]:
    """
    Returns a list of tuples where the elements are the index of the topic, the
    number of datasets that belong to that topic, the color assigned to the
    topic, and the keywords for the topic, in that order.

    :param cluster_topics: List of lists of keywords for each topic.
    :param datasests_df: A pandas dataframe that contains information about the
    datasets and their cluster assignements.
    """
    n_topics = len(cluster_topics)
    topic_colors = get_topic_colors(n_topics)
    topic_counts = datasets_df.groupby("cluster")["id"].count()
    return [
        (index + 1, topic_counts[index], topic_colors[index], ", ".join(topics))
        for index, topics in enumerate(cluster_topics)
    ]