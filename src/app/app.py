import json
from typing import List, Tuple
import pandas as pd
from flask import Flask, render_template, request, abort
from src.analysis.analyzer import DatasetAnalyzer
from src.visualization.visualize_clusters import visualize_clusters, get_topic_colors
from src.config import config
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError

app = Flask(__name__)
svd_dimensions = config.svd_dimensions


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/visualize", methods=["POST"])
def visualize_pubmed_ids():
    try:
        pubmed_ids = json.loads(request.form["pubmed_ids"])
        n_ids = len(pubmed_ids)
        n_clusters = int(request.form["n_clusters"])
    except ValueError as e:
        app.logger.error(e)
        abort(400)

    try:
        analyzer = DatasetAnalyzer(svd_dimensions, n_clusters)
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
    except NotEnoughDatasetsError as _:
        return render_template(
            "index.html",
            pubmed_ids=pubmed_ids,
            n_clusters=n_clusters,
            short_error_message="Too few PubMed IDs",
            full_error_message="Not enough datasests are associated with the PubMed IDs. Please add more PubMed IDs.",
        ), 400
    except Exception as e:
        app.logger.error(e)
        return render_template(
            "index.html",
            pubmed_ids=pubmed_ids,
            n_clusters=n_clusters,
            short_error_message="An error occured",
            full_error_message="An error occured on our end. Please try again.",
        ), 500

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
        (index, topic_counts[index], topic_colors[index], ", ".join(topics))
        for index, topics in enumerate(cluster_topics)
    ]
