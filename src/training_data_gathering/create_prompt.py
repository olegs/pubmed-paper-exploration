from argparse import ArgumentParser
import asyncio
import json
from typing import List

import aiohttp
import pandas as pd
from jinja2 import Template

from src.ingestion.download_related_paper_datasets import \
    download_related_paper_datasets
from src.ingestion.download_samples import download_samples
from src.model.geo_dataset import GEODataset
from src.model.geo_sample import GEOSample


async def download_samples_for_datasets(datasets: List[GEODataset]) -> List[GEOSample]:
    """
    Downloads GEO samples that are associated with the specified datasets.
    This function sets the samples field for each of the passed datasets.

    :param datasets: Datasets for which to download samples
    :reutrn: List of samples contained in the datasets.
    """
    samples = set()  # We are using a set because some samples can occur twice. For example, a sample appears twice when it is in a subseries and superseries
    async with aiohttp.ClientSession() as session:
        for series in datasets:
            try:
                series.samples = await download_samples(series, session)
            except aiohttp.ServerDisconnectedError:
                session = await session.close()
                session = aiohttp.ClientSession()
                series.samples = await download_samples(series, session)
            finally:
                if series.samples is not None:
                    samples.update(series.samples)
                else:
                    print("Samples is none for series:", series.id)
    return samples

def download_samples_from_pubtrends_export(pubtrends_export_path):
    paper_export = json.load(
        open(pubtrends_export_path))
    datasets = download_related_paper_datasets(paper_export)
    samples = asyncio.run(download_samples_for_datasets(datasets))

    accessions = [sample.accession for sample in samples]
    assert len(set(accessions)) == len(samples)
    return list(samples)


if __name__ == "__main__":
    import os
    argument_parser = ArgumentParser(description="Writes gemini prompts for linking tissues and cell types to MeSH terms. The tissues and cell types are read from datasets of papers in the passed PubTrends JSON export.")
    argument_parser.add_argument("--pubtrends_export_paths", nargs="+")
    argument_parser.add_argument("--output_path")
    args = argument_parser.parse_args()


    samples = set()
    for path in args.pubtrends_export_paths:
        samples.update(download_samples_from_pubtrends_export(path))

    tissues = list({sample.characteristics["tissue"].strip()
                        for sample in samples if "tissue" in sample.characteristics})

    cell_types = list({sample.characteristics["cell type"].strip()
                  for sample in samples if "cell type" in sample.characteristics})
                
    tissues_or_cell_types = list(set(tissues + cell_types))
    print("Number of unique tissues and cell types", len(tissues_or_cell_types))

    mesh_terms = pd.read_csv("mesh_terms.csv")
    mesh_terms = zip(mesh_terms["mesh_id"], mesh_terms["term"])

    prompt_template: Template = None
    with open(os.path.join("src", "training_data_gathering","prompt_template.txt"), "r") as f:
        prompt_template = Template(f.read())

    prompt = prompt_template.render(mesh_terms=mesh_terms, tissues_or_cell_types=tissues_or_cell_types)

    with open(args.output_path, "w") as f:
        f.write(prompt)

