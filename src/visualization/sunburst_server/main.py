from random import random
from typing import List

from bokeh.layouts import row, column
from bokeh.models import Button, Select, MultiChoice
from bokeh.models.renderers.glyph_renderer import GlyphRenderer
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc
import pickle
from src.analysis.analysis_result import AnalysisResult
from src.visualization.sunburst_server.plot_sunburst import plot_sunburst
from src.visualization.sunburst_server.hierarchical_data_counter import HierarchicalDataCounter

NUMBER_OF_LEVELS_TO_DISPLAY = 2
current_zoom_level = 1

args = curdoc().session_context.request.arguments
job_id = args.get("job-id")[0].decode("ascii")
job_id = job_id[:job_id.find("?")][:job_id.find("/")]
print("Job ID:", job_id)

results: AnalysisResult = None
with open(f"completed_jobs/{job_id}.pkl", "rb") as f:
    results = pickle.load(f)


def get_entity_name(hierarchy_col):
    return hierarchy_col \
        .replace("_hierarchy", "")\
        .replace("_", " ")\
        .title()


def get_hierarchy_column_name(entity_name):
    return entity_name\
        .lower()\
        .replace(" ", "_")\
        + "_hierarchy"


def get_selectable_entities(results_df):
    hierarchy_columns = list(
        filter(lambda col: col.endswith("hierarchy"), results_df.columns))
    selectable_entities = []
    for hierarchy_col in hierarchy_columns:
        term_hierarchies = [
            hierarchy for sublist in results.df[hierarchy_col] for hierarchy in sublist]
        if any(len(term_hierarchy) != 0 for term_hierarchy in term_hierarchies):
            entity = hierarchy_col.replace(
                "_hierarchy", "").replace("_", " ").title()
            selectable_entities.append(entity)

    return selectable_entities


def flatten(l):
    return [item for sublist in l for item in sublist]


def flatten_unique(l):
    return list({item for sublist in l for item in sublist})


def is_nested(l: List):
    return isinstance(l[0], list)


selectable_entities = get_selectable_entities(results.df)
initial_col_name = get_hierarchy_column_name(selectable_entities[0])


def preproccess_entity_hierarchies(entity_name, zoom_level):
    column_name = get_hierarchy_column_name(entity_name)
    term_hierarchies = results.df[column_name].tolist()
    representative_row = max(term_hierarchies, key=len)
    print(representative_row)
    if is_nested(representative_row):
        term_hierarchies = flatten(term_hierarchies)

    hierarchical_data_counter = HierarchicalDataCounter(term_hierarchies)
    plot_df = hierarchical_data_counter.get_df_at_levels(
        list(range(zoom_level, zoom_level + NUMBER_OF_LEVELS_TO_DISPLAY)))
    return plot_df


plot_df = preproccess_entity_hierarchies(
    selectable_entities[0], current_zoom_level)
sunburst_plot = plot_sunburst(plot_df, "Something" + "s")

group_by_select = Select(
    title="Group by:", value=selectable_entities[0], options=selectable_entities)
species_multi_choice = MultiChoice(title="Species", value=[
], options=flatten_unique(results.df["organisms"].tolist()))
experiment_type_multi_choice = MultiChoice(title="Experiment type", value=[
], options=results.df["experiment_type"].unique().tolist())
grouped_vaule_choice = MultiChoice(title=selectable_entities[0], value=[
], options=flatten(results.df[initial_col_name].tolist()))


def group_by_select_on_change(attr, old, new):
    global current_zoom_level
    current_zoom_level = 1
    new_plot_df = preproccess_entity_hierarchies(new, current_zoom_level)
    new_plot = plot_sunburst(new_plot_df, new + "s")
    new_data = new_plot.select(type=GlyphRenderer)[0].data_source.data
    for glyph in sunburst_plot.select(type=GlyphRenderer):
        glyph.data_source.data = dict(new_data)


group_by_select.on_change("value", group_by_select_on_change)


# put the button and plot in a layout and add to the document
curdoc().add_root(row(sunburst_plot, column(group_by_select,
                                            species_multi_choice, experiment_type_multi_choice)))
