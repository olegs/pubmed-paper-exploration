# geo-dataset-clustering
This repository contains a web app which takes a set of PubMed IDs and clusters datasets in the [GEO database](https://www.ncbi.nlm.nih.gov/gds/) that are associated with those PubMed IDs based on text similarity.

The app was built using [flask](https://flask.palletsprojects.com/en/stable/) and [bokeh](https://bokeh.org/).

## Prerequisites
- Python 3.10 or higher
- R 4.3 or higher
- pip
- venv



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
4. Download a copy of the MeSH vocabulary. You can download it by running this command:
```bash 
wget -O desc2025.xml https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2025.xml
```
5. Download a copy of the NCBI Gene vocabulary. You can download it by running the following commands:
```bash
wget https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
gunzip <Homo_sapiens.gene_info.gz > Homo_sapiens.gene_info
python -m src.standardization.generate_ncbi_gene_map Homo_sapiens.gene_info gene_ontology_map.json
```
6. Generate the mapping between GPL numbers and platfrom names by running this R script (may take a while)
```bash
R < get_gpl_names.R
mv gpl_platform_map.json src/model/gpl_platform_map.json
```
7. Clone [PubTrends](https://github.com/jetBrains-Research/pubtrends/) and launch the fasttext container
```bash
git clone https://github.com/jetBrains-Research/pubtrends/
cd pubtrends
docker compose up -f docker-compose.fasttext -d
cd ..
```
8. Launch the flask app
```bash
python -m flask --app src.app.app run
```
9. Launch the bokeh server
```bash
python -m bokeh serve --allow-websocket-origin=localhost --allow-websocket-origin=localhost:5006 --show src/visualization/sunburst_server
```
10. Run nginx
```bash
docker compose up -d
```

The app can now accessed at `localhost/app` on port 80.

## Configuration options
- `download_folder`: The path to which to download the GEO datasets.
- `svd_dimensions`: The number of dimensions to which to reduce the tf-idf representations of the datasets.
- `topic_words`: The number of keywords to extract for cluster/topic. It must be at least 5.
- `log_level`: Logging level. It can be one of: `DEBUG`, `INFO`, `WARNING` or `ERROR`.
- `BERN2.url`: URL to the BERN2 API endpoint
- `BERN2.rate_limit`: Maximum number of requests per second to the BERN2 API endpoint
- `search.backend`: Which API to use to search for papers. Can be either `pubtrends` or `esearch`. ESearch is generally faster.


