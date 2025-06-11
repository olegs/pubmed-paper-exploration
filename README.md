# geo-dataset-clustering
This repository contains a web app which takes a set of PubMed IDs and clusters datasets in the [GEO database](https://www.ncbi.nlm.nih.gov/gds/) that are associated with those PubMed IDs based on text similarity.

The app was built using [flask](https://flask.palletsprojects.com/en/stable/) and [bokeh](https://bokeh.org/).

## Prerequisites
- Python 3.10 or higher
- pip
- venv
- A copy of the MeSH vocabulary. You can download it by running this command:
```bash 
wget -O desc2025.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml
```


## Launch instructions
1. Create a virtual environment:
```bash
python -m venv .venv
```
2. Activate the virtual environment:
```bash
source .venv/bin/activate
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Launch the flask app
```bash
python -m flask --app src.app.app run
```

## Configuration options
- `download_folder`: The path to which to download the GEO datasets.
- `svd_dimensions`: The number of dimensions to which to reduce the tf-idf representations of the datasets.
- `topic_words`: The number of keywords to extract for cluster/topic. It must be at least 5.
- `log_level`: Logging level. It can be one of: `DEBUG`, `INFO`, `WARNING` or `ERROR`.
