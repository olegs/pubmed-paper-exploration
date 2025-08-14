from random import random
from typing import List

from bokeh.layouts import row, column
from bokeh.models import Select, MultiChoice, ColumnDataSource, CustomJS, Styles
from bokeh.models.renderers.glyph_renderer import GlyphRenderer
from bokeh.palettes import RdYlBu3
from bokeh.plotting import curdoc
import pickle
from src.analysis.analysis_result import AnalysisResult
from src.visualization.sunburst_server.plot_sunburst import plot_sunburst, update_plot_data, set_category_name
from src.visualization.sunburst_server.hierarchical_data_counter import HierarchicalDataCounter
from src.visualization.sunburst_server.contains_name_at_level_filter import ContainsNameAtLevelFilter
from src.visualization.sunburst_server.value_in_cell_filter import AnyValueInCellFilter

NUMBER_OF_LEVELS_TO_DISPLAY = int(2)


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


def flatten(l):
    return [item for sublist in l for item in sublist]


def flatten_unique(l):
    return list({item for sublist in l for item in sublist})


def is_nested(l: List):
    return isinstance(l[0], list)


class InteractiveSunburst:
    def __init__(self, results: AnalysisResult):
        self.df = results.df
        self.entity = self.get_selectable_entities()[0]
        self.zoom_levels = []
        self.zoom_filters = []
        self.value_filters = {}
        self.plot = plot_sunburst(
            self.preprocess_entity_hierarchies(), self.get_title(), self.entity, lambda row: self._click_callback(row), lambda: self._zoom_out_callback())

        # A dummy data source for sending updated data to the frontend using
        # BokehJS events
        self.df_ds = ColumnDataSource(self.df)
        self.df_ds.js_on_change("data", CustomJS(
            args=dict(source=self.df_ds), code="refreshTable(source.data);"))
        self.plot.scatter(x="x", y="y", size=0, source=self.df_ds)

    def _get_filtered_df(self):
        df = self.df.copy()
        for filter in self.zoom_filters + list(self.value_filters.values()):
            df = filter(df)
        
        return df

    def _click_callback(self, row):
        new_zoom_level = self.zoom_level + row["level"]
        self.zoom_in(new_zoom_level, row["name"])

    def _zoom_out_callback(self):
        if self.zoom_level <= 1:
            return
        self.zoom_out()

    def zoom_out(self):
        if self.zoom_filters:
            self.zoom_filters.pop()
        if self.zoom_levels:
            self.zoom_levels.pop()
        self._redraw()

    def is_zoom_valid(self):
        return len(self.preprocess_entity_hierarchies()) != 0

    def zoom_in(self, new_zoom_level: int, category: str):
        current_entity_column = get_hierarchy_column_name(self.entity)
        self.zoom_levels.append(new_zoom_level)
        self.zoom_filters.append(ContainsNameAtLevelFilter(
            category, new_zoom_level-1, current_entity_column))
        if self.is_zoom_valid():
            self._redraw()
        else:
            self.zoom_levels.pop()
            self.zoom_filters.pop()

    def get_title(self):
        return self.entity + "s"

    @property
    def zoom_level(self):
        if self.zoom_levels:
            return self.zoom_levels[-1]
        return 1

    def preprocess_entity_hierarchies(self):
        column_name = get_hierarchy_column_name(self.entity)
        df = self._get_filtered_df()
        term_hierarchies = df[column_name].tolist()
        representative_row = max(term_hierarchies, key=len)
        if is_nested(representative_row):
            term_hierarchies = flatten(term_hierarchies)

        hierarchical_data_counter = HierarchicalDataCounter(term_hierarchies)
        plot_df = hierarchical_data_counter.get_df_at_levels(
            list(range(self.zoom_level, self.zoom_level + NUMBER_OF_LEVELS_TO_DISPLAY)))
        return plot_df

    def _set_category_name_in_plot(self):
        subcategory_name = self.zoom_filters[-1].name if self.zoom_filters else ""
        if subcategory_name:
            set_category_name(self.plot, self.entity, subcategory_name)
            return
        set_category_name(self.plot, self.entity)

    def _redraw(self):
        new_plot_df = self.preprocess_entity_hierarchies()
        update_plot_data(self.plot, new_plot_df)
        self._set_category_name_in_plot()
        self.plot.title = self.entity + "s"
        self._send_data_to_frontend()

    def _send_data_to_frontend(self):
        updated_ds = ColumnDataSource(self._get_filtered_df())
        self.df_ds.data = dict(updated_ds.data)

    def set_entity(self, entity):
        self.zoom_levels = []
        self.zoom_filters = []
        self.entity = entity
        self._redraw()

    def get_selectable_entities(self):
        hierarchy_columns = list(
            filter(lambda col: col.endswith("hierarchy"), self.df.columns))
        selectable_entities = []
        for hierarchy_col in hierarchy_columns:
            term_hierarchies = [
                hierarchy for sublist in results.df[hierarchy_col] for hierarchy in sublist]
            if any(len(term_hierarchy) != 0 for term_hierarchy in term_hierarchies):
                entity = hierarchy_col.replace(
                    "_hierarchy", "").replace("_", " ").title()
                selectable_entities.append(entity)

        return selectable_entities

    def add_value_filter(self, column, value):
        if column in self.value_filters:
            self.value_filters[column].values.append(value)
        else:
            self.value_filters[column] = AnyValueInCellFilter(column, [value])
        self._redraw()

    def remove_value_filter(self, column, value):
        if column not in self.value_filters:
            return
        self.value_filters[column].values.remove(value)
        self._redraw()


args = curdoc().session_context.request.arguments
job_id = args.get("job-id")[0].decode("ascii")
job_id = job_id[:job_id.find("?")][:job_id.find("/")]
print("Job ID:", job_id)

results: AnalysisResult = None
with open(f"completed_jobs/{job_id}.pkl", "rb") as f:
    results = pickle.load(f)

interactive_sunburst = InteractiveSunburst(results)


selectable_entities = interactive_sunburst.get_selectable_entities()
initial_col_name = get_hierarchy_column_name(selectable_entities[0])

input_style = Styles(width="15rem")
group_by_select = Select(
    title="Group by:", value=selectable_entities[0], options=selectable_entities, styles=input_style)
organism_multi_choice = MultiChoice(title="Organism", value=[
], options=flatten_unique(results.df["organisms"].tolist()), styles=input_style)
experiment_type_multi_choice = MultiChoice(title="Experiment type", value=[
], options=results.df["experiment_type"].unique().tolist(), styles=input_style)


def group_by_select_on_change(attr, old, new):
    interactive_sunburst.set_entity(new)

group_by_select.on_change("value", group_by_select_on_change)


def get_removed_value(old_values, new_values):
    old = set(old_values)
    new = set(new_values)
    return old.difference(new).pop()

def experiment_type_multi_choice_on_change(attr, old, new):
    if len(new) > len(old):
        interactive_sunburst.add_value_filter("experiment_types", new[-1])
        return
    removed_value = get_removed_value(old, new)
    interactive_sunburst.remove_value_filter("experiment_types", removed_value)

experiment_type_multi_choice.on_change("value", experiment_type_multi_choice_on_change)


def organism_multi_choice_on_change(attr, old, new):
    if len(new) > len(old):
        interactive_sunburst.add_value_filter("organisms", new[-1])
        return
    removed_value = get_removed_value(old, new)
    interactive_sunburst.remove_value_filter("organisms", removed_value)

organism_multi_choice.on_change("value", organism_multi_choice_on_change)


# put the button and plot in a layout and add to the document
curdoc().add_root(row(interactive_sunburst.plot, column(group_by_select,
                                                        organism_multi_choice, experiment_type_multi_choice)))
