import traceback
import json
from typing import List, Tuple
import pandas as pd
from flask import Flask, render_template, request, abort, jsonify
from src.analysis.analyzer import DatasetAnalyzer
from src.visualization.visualize_clusters import visualize_clusters_html
from src.visualization.get_topic_table import get_topic_table
from src.config import config
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
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
        result = analyzer.analyze_paper_datasets(pubmed_ids)
        n_datasets = len(result.df)

        clustering_html = visualize_clusters_html(result.df, result.cluster_topics)
        topic_table = get_topic_table(result.cluster_topics, result.df)

        return render_template(
            "visualization.html",
            clustering_html=clustering_html,
            n_ids=n_ids,
            n_datasets=n_datasets,
            topic_table=topic_table,
            datasets_json = result.datasets_list
        )
    except NotEnoughDatasetsError as _:
        return render_template(
            "index.html",
            pubmed_ids=pubmed_ids,
            n_clusters=n_clusters,
            short_error_message="Too few PubMed IDs",
            full_error_message="Not enough datasests are associated with the PubMed IDs. Please add more PubMed IDs.",
        ), 400
    except Exception:
        app.logger.error(traceback.format_exc())
        return render_template(
            "index.html",
            pubmed_ids=pubmed_ids,
            n_clusters=n_clusters,
            short_error_message="An error occured",
            full_error_message="An error occured on our end. Please try again.",
        ), 500

