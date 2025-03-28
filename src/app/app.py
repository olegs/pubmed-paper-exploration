import json
from flask import Flask, render_template, request
from markupsafe import escape
from src.analysis.analyzer import DatasetAnalyzer
from src.visualization.visualize_clusters import visualize_clusters, get_topic_colors
from typing import List, Tuple
import pandas as pd

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/visualize", methods=["POST"])
def visualize_pubmed_ids():
    pubmed_ids = json.loads(request.form["pubmed_ids"])
    n_ids = len(pubmed_ids)

    analyzer = DatasetAnalyzer(15, 10)
    result = analyzer.analyze_datasets(pubmed_ids)
    n_datasets = len(result.df)

    clustering_html = visualize_clusters(result.df, result.cluster_topics)
    topic_table = get_topic_table(result.cluster_topics, result.df)

    return render_template(
        "visualization.html",
        clustering_html=clustering_html,
        n_ids=n_ids,
        n_datasets=n_datasets,
        topic_table=topic_table,
    )


def get_topic_table(cluster_topics: List[List[str]], datasets_df: pd.DataFrame) -> List[Tuple[int, int, str, str]]:
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
    print(topic_counts)
    return [
        (index,  topic_counts[index], topic_colors[index], ", ".join(topics)) for index, topics in enumerate(cluster_topics)
    ]
