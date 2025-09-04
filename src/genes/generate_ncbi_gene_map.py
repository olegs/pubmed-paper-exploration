import argparse
import json

import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("gene_ontology_path")  # Homo_sapiens.gene_info from NCBI Gene
    parser.add_argument("output_path")
    args = parser.parse_args()

    gene_ontology = pd.read_csv(args.gene_ontology_path, sep="\t")
    print(gene_ontology.head())
    gene_ontology_json = {}

    for id, row in gene_ontology.iterrows():
        gene_ontology_json[f"NCBIGene:{row['GeneID']}"] = row['Full_name_from_nomenclature_authority']

    with open(args.output_path, "w") as f:
        json.dump(gene_ontology_json, f, indent=2)
