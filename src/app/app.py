from flask import Flask, render_template
from markupsafe import escape
from src.analysis.analyzer import DatasetAnalyzer
from src.visualization.visualize_clusters import visualize_clusters

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("hello.html")
