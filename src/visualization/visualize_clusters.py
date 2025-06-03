from string import Template
from typing import List, Tuple
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Text, HoverTool
from bokeh.palettes import Category10, Category20
from bokeh.transform import factor_cmap
from bokeh.embed import components
import pandas as pd


def get_topic_colors(n_topics) -> List[str]:
    """
    Returns the list of colors used for color-coding the topics.

    :param n_topics: Number of topics.
    :return: List of strings containing the hex codes for the colors.
    """
    if n_topics <= 10:
        return Category10[n_topics]

    return Category20[n_topics]


def get_html_tooltips(tooltips: List[Tuple[str, str]]):
    """
    Generates the HTML for the dataset tooltips.
    Based on __paper_html_tooltips from PubTrends.

    :param tooltips: List of tuples that contains the captions and values for
    the tooltips like the one passed to Bokeh"s figure function.
    :return: String containing the HTML.
    """
    style_caption = Template(
        '<span style="font-size: 12px; color:dodgerblue;">$caption:</span>'
    )
    style_value = Template('<span style="font-size: 11px;">$value</span>')

    tooltips_items_html = "\n".join(
        [
            f"<div>{style_caption.substitute(caption=tooltip[0])} {style_value.substitute(value=tooltip[1])}</div>"
            for tooltip in tooltips
        ]
    )

    return f"""
        <div style="max-width: 15vw">
            <span style="font-size:14px; font-weight:bold;">@title</span>
            {tooltips_items_html}
        </div>
    """


def _plot_cluster_centers(plot, datasets_df: pd.DataFrame):
    """
    Plots cluster centers.

    :param plot: Bokeh figure where the datasets are visualized.
    :param datasets_df: A pandas dataframe which contains the infromation about the
    datasets, the cluster they are assigned to in the "cluster" column, and
    their coordianates in a 2D space ("x" and "y" columns).
    """
    cluster_centers = datasets_df.groupby(["cluster"])[["x", "y"]].mean()
    source = ColumnDataSource(cluster_centers)
    source.data["cluster"] = list(map(lambda x: f"#{x}", source.data["cluster"] + 1))
    glyph = Text(
        x="x",
        y="y",
        text="cluster",
        text_font_size="14px",
        background_fill_color="#eeeeee",
        background_fill_alpha=0.6,
        padding=1
    )
    plot.add_glyph(source, glyph)


def visualize_clusters_html(datasets_df: pd.DataFrame, cluster_topics: List[List[str]]):
    """
    Visualizes the result of the dataset clustering and outputs the
    visualization as HTML and Javascript.

    :param datasets_df: A pandas dataframe which contains the infromation about the
    datasets, the cluster they are assigned to in the "cluster" column, and
    their coordianates in a 2D space ("x" and "y" columns).
    :param cluster_topics: List of lists of keywords for each topic.
    :return: A string containing the HTML that renders the plot.
    """

    cluster_visualization = _visualize_clusters(datasets_df, cluster_topics)
    script, div = components(cluster_visualization)
    return f"{script}\n{div}"


def _visualize_clusters(datasets_df: pd.DataFrame, cluster_topics: List[List[str]]) -> figure:
    """
    Visualizes the result of the dataset clustering and outputs the
    visualization as a bokeh figure.

    :param datasets_df: A pandas dataframe which contains the infromation about the
    datasets, the cluster they are assigned to in the "cluster" column, and
    their coordianates in a 2D space ("x" and "y" columns).
    :param cluster_topics: List of lists of keywords for each topic.
    :return: A bokeh figure containing the plot.
    """
    number_of_topic_words_to_display = 5
    source = ColumnDataSource(datasets_df)
    source.data["cluster"] = list(map(str, source.data["cluster"] + 1))
    source.add(
        list(
            map(
                lambda x: ", ".join(
                    cluster_topics[x][:number_of_topic_words_to_display]
                ),
                datasets_df["cluster"],
            )
        ),
        "topics",
    )

    cluster_visualization = figure(
        width=1000,
        height=1000,
        sizing_mode="scale_width",
        tools=[
            "pan",
            "box_zoom",
            "wheel_zoom",
            "save",
            "reset",
            "help"
        ],
    )
    hover_tool = HoverTool(
        tooltips=get_html_tooltips(
            [
                ("ID", "@id"),
                ("Organism", "@organisms"),
                ("Topic", "@cluster"),
                ("Topic tags", "@topics"),
                ("Pubmed IDs", "@pubmed_ids"),
            ]
        )
    )
    cluster_visualization.add_tools(hover_tool)
    n_topics = len(cluster_topics)
    scatter = cluster_visualization.scatter(
        source=source,
        x="x",
        y="y",
        size=12,
        color=factor_cmap(
            "cluster",
            get_topic_colors(n_topics),
            list(map(str, list(range(1, n_topics + 1)))),
        ),
        alpha=0.8,
        marker="circle",
    )
    _plot_cluster_centers(cluster_visualization, datasets_df)

    cluster_visualization.xaxis.major_tick_line_color = None
    cluster_visualization.xaxis.minor_tick_line_color = None
    cluster_visualization.xaxis.major_label_text_font_size = "0pt"
    cluster_visualization.xgrid.visible = False

    cluster_visualization.yaxis.major_tick_line_color = (
        None  # turn off y-axis major ticks
    )
    cluster_visualization.yaxis.minor_tick_line_color = (
        None  # turn off y-axis minor ticks
    )
    cluster_visualization.yaxis.major_label_text_font_size = (
        "0pt"  # turn off x-axis tick labels
    )
    cluster_visualization.ygrid.visible = False

    hover_tool.renderers = [scatter]
    return cluster_visualization



if __name__ == "__main__":
    from src.analysis.analyzer import DatasetAnalyzer

    with open("ids.txt") as file:
        pubmed_ids = map(int, file)
        analyzer = DatasetAnalyzer(15, 10)
        result = analyzer.analyze_paper_datasets(pubmed_ids)
        print(visualize_clusters_html(result.df, result.cluster_topics))
