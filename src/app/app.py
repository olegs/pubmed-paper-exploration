import traceback
import json
import uuid
import os.path as path
import os
from flask import Flask, render_template, request, abort, Blueprint, url_for
from src.analysis.analyzer import DatasetAnalyzer
from src.analysis.analysis_result import AnalysisResult
from src.visualization.visualize_clusters import visualize_clusters_html
from src.visualization.get_topic_table import get_topic_table
from src.config import config
from src.exception.not_enough_datasets_error import NotEnoughDatasetsError
from src.tissue_and_cell_type_standardization.is_mesh_term_in_anatomy_or_disease import build_mesh_lookup
from src.ingestion.get_pubmed_ids import get_pubmed_ids_esearch, get_pubmed_ids
import pickle
from bokeh.embed import server_document
from flask_cors import CORS, cross_origin
from bokeh.embed import server_document
import csv
import asyncio


app = Flask(__name__)
cors = CORS(app, origins=["http://localhost:5006"])
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
bp = Blueprint('app', __name__,
               template_folder='templates',
               static_folder="static")


svd_dimensions = config.svd_dimensions
mesh_lookup = build_mesh_lookup("desc2025.xml")
ncbi_gene = {}
with open("gene_ontology_map.json") as f:
    ncbi_gene = json.load(f)
analyzer = DatasetAnalyzer(svd_dimensions, mesh_lookup, ncbi_gene)


@bp.route("/")
def index():
    return render_template("index.html")


def save_result(result):
    if not path.isdir("completed_jobs"):
        os.mkdir("completed_jobs")
    job_id = str(uuid.uuid4())
    with open(f"completed_jobs/{job_id}.pkl", "wb") as f:
        pickle.dump(result, f)
    result.df.to_csv(f"completed_jobs/{job_id}_df.csv", quotechar='"', quoting=csv.QUOTE_NONNUMERIC) 
    if result.samples:
        result.samples.to_csv(f"completed_jobs/{job_id}_samples.csv")
    return job_id


def load_result(job_id) -> AnalysisResult:
    try:
        with open(f"completed_jobs/{job_id}.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


@bp.route("/visualize", methods=["GET"])
@cross_origin()
def visualize_completed_job():
    job_id = request.args.get("job-id")
    if not job_id:
        abort(400)

    result: AnalysisResult = load_result(job_id)
    if not result:
        abort(404)

    n_datasets = len(result.df)
    # FIXME: Store pubmed_ids in analysis result
    n_ids = len(set(
        pubmed_id for dataset in result.datasets_list for pubmed_id in dataset["pubmed_ids"]))
    clustering_html = visualize_clusters_html(result.df, result.cluster_topics)
    topic_table = get_topic_table(result.cluster_topics, result.df)
    host = request.headers.get("Host")
    sunburst_plot = server_document(
        f"http://{host}/sunburst_server?job-id={job_id}")

    return render_template(
        "visualization.html",
        clustering_html=clustering_html,
        n_ids=n_ids,
        n_datasets=n_datasets,
        topic_table=topic_table,
        datasets_json=result.datasets_list,
        sunburst_plot=sunburst_plot,
        n_clusters=result.n_clusters
    )


@bp.route("/visualize", methods=["POST"])
@cross_origin()
def visualize_pubmed_ids():
    try:
        pubmed_ids = None
        if request.form.get("pubmed_ids") and request.form.get("pubmed_ids") != "[]":
            pubmed_ids = json.loads(request.form["pubmed_ids"])
        elif request.form.get("query"):
            pubmed_ids = None
            for _ in range(3):
                try:
                    pubmed_ids = asyncio.run(get_pubmed_ids_esearch(request.form["query"]))
                    break
                except Exception as e:
                    continue
            app.logger.info(f"Found {len(pubmed_ids)} for {request.form['query']}")
        else:
            app.logger.error(f"Neither query nor pubmed ids specified")
            abort(400)
        n_ids = len(pubmed_ids)
    except ValueError as e:
        app.logger.error(f"ValueError: {e}")
        abort(400)

    try:
        result = analyzer.analyze_paper_datasets(pubmed_ids)
        n_datasets = len(result.df)

        job_id = save_result(result)

        clustering_html = visualize_clusters_html(
            result.df, result.cluster_topics)
        topic_table = get_topic_table(result.cluster_topics, result.df)
        host = request.headers.get("Host")
        sunburst_plot = server_document(
            f"http://{host}/sunburst_server?job-id={job_id}")

        return render_template(
            "visualization.html",
            clustering_html=clustering_html,
            n_ids=n_ids,
            n_datasets=n_datasets,
            topic_table=topic_table,
            datasets_json=result.datasets_list,
            sunburst_plot=sunburst_plot,
            n_clusters=result.n_clusters
        )
    except NotEnoughDatasetsError as _:
        app.logger.error(f"Not enough datasets for {len(pubmed_ids)} PubMed IDs")
        return render_template(
            "index.html",
            pubmed_ids=pubmed_ids,
            short_error_message="Too few PubMed IDs",
            full_error_message="Not enough datasests are associated with the PubMed IDs. Please add more PubMed IDs.",
        ), 400
    except Exception:
        app.logger.error(traceback.format_exc())
        return render_template(
            "index.html",
            pubmed_ids=pubmed_ids,
            short_error_message="An error occured",
            full_error_message="An error occured on our end. Please try again.",
        ), 500


app.register_blueprint(bp, url_prefix='/app')
