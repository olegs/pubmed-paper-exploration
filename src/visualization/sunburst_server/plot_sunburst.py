import pandas as pd
import numpy as np
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category20c
from textwrap import wrap
import colorcet as cc


data = {
    'id': ['/lib', '/home', '/home/user', '/home/user/data', '/home/user/docs', '/tmp'],
    'parent': ['', '', '/home', '/home/user', '/home/user', ''],
    'name': ['lib', 'home', 'user', 'data', 'docs', 'tmp'],
    'value': [25, 0, 0, 40, 35, 25] # Values for children
}
df = pd.DataFrame(data)

def calculate_angles_and_radii(df, ring_width, root_id=""):
    """ 
    Calculates angles and radii for the sunburst chart. 
    Also calculates values for non-leaf nodes.
    The values of internal nodes are calculated as the sum
    of their descendants' values.
    """
    # Work on a copy to avoid modifying the original DataFrame
    plot_df = df.copy()

    # Initialize columns
    plot_df['angle'] = 0.0
    plot_df['start_angle'] = 0.0
    plot_df['end_angle'] = 0.0
    plot_df['inner_radius'] = 0.0
    plot_df['outer_radius'] = 0.0

    total_value = plot_df.loc[plot_df.parent == "", "value"].sum()

    plot_df["angle"] = plot_df["value"] / total_value * 2 * np.pi

    plot_df = plot_df.sort_values(by="value", ascending=False)

    def calculate_angles(parent_id, start_angle, level):
        children = plot_df[plot_df['parent'] == parent_id]
        current_angle = start_angle
        
        for idx, child in children.iterrows():
            plot_df.loc[idx, 'start_angle'] = current_angle
            end_angle = current_angle + child['angle']
            plot_df.loc[idx, 'end_angle'] = end_angle
            
            plot_df.loc[idx, 'inner_radius'] = level*ring_width
            plot_df.loc[idx, 'outer_radius'] = level*ring_width + ring_width
            
            calculate_angles(child['id'], current_angle, level + 1)

            current_angle = end_angle

    calculate_angles(root_id, 0, 1) # Start at level 1

    return plot_df



def add_wedge_color(plot_df, root_id=""):
    plot_df = plot_df.copy()
    # Create a color map
    # Note: Use a larger palette if you have more top-level categories
    plot_df["color"] = "#000000"
    number_of_categories = len(plot_df[plot_df['parent'] == root_id])
    palette = None
    if number_of_categories <= 20:
        palette = Category20c[max(number_of_categories, 3)]
    else:
        palette = cc.glasbey[:number_of_categories]

    for i, row in enumerate(plot_df[plot_df["parent"] == root_id].iterrows()):
        idx, _ = row
        plot_df.loc[idx, "color"] = palette[i]

    def _add_color(parent_id, color):
        children = plot_df[plot_df['parent'] == parent_id]
        
        for idx, child in children.iterrows():
            if color is not None:
                plot_df.loc[idx, "color"] = color

            _add_color(child['id'], plot_df.loc[idx, "color"])

    _add_color(root_id, None) # Start at level 1
    return plot_df

def get_contrasting_text_color(hex_color):
    """
    Calculates whether black or white text is more readable against a given
    hex background color.
    
    Args:
        hex_color (str): The background color in hex format (e.g., "#RRGGBB").
        
    Returns:
        str: "white" or "black".
    """
    hex_color = hex_color.lstrip('#')
    r_int, g_int, b_int = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    
    # Calculate luminance
    # Formula from WCAG guidelines: https://www.w3.org/TR/WCAG20-TECHS/G17.html
    rgb = []
    for c_int in [r_int, g_int, b_int]:
        c = c_int / 255.0
        if c <= 0.03928:
            c = c / 12.92
        else:
            c = ((c + 0.055) / 1.055) ** 2.4
        rgb.append(c)
        
    luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    
    return 'black' if luminance > 0.5 else 'white'

def calculate_text_positions(plot_df):
    plot_df = plot_df.copy()
    center_angle = (plot_df['start_angle'] + plot_df['end_angle']) / 2
    center_radius = (plot_df['inner_radius'] + plot_df['outer_radius']) / 2

    plot_df['text_x'] = center_radius * np.cos(center_angle)
    plot_df['text_y'] = center_radius * np.sin(center_angle)
    plot_df['text_angle'] = center_angle
    # Flip texts in the left half of the sunburst so they do not appear upside down
    plot_df.loc[plot_df["text_angle"].between(np.pi/2, 3 * np.pi/2), "text_angle"] += np.pi
    return plot_df

def add_text_color(plot_df):
    plot_df = plot_df.copy()
    plot_df["text_color"] = plot_df["color"].map(get_contrasting_text_color)
    return plot_df


def process_data_for_sunburst(df, ring_width, root_id=""):
    plot_df = calculate_angles_and_radii(df, ring_width, root_id)
    plot_df = add_wedge_color(plot_df, root_id)
    plot_df = calculate_text_positions(plot_df)
    plot_df = add_text_color(plot_df)
    return plot_df



def plot_sunburst(df, title, ring_width=0.8, max_text_width=23, root_id=""):
    plot_df = process_data_for_sunburst(df, ring_width, root_id)
    plot_df["name"] = plot_df["name"].map(lambda name: "\n".join(wrap(name, width=max_text_width)))
    source = ColumnDataSource(plot_df)

    p = figure(
        width=600, 
        height=600, 
        title=title,
        x_axis_type=None, 
        y_axis_type=None,
        x_range=(-4, 4), 
        y_range=(-4, 4),
        min_border=0,
        outline_line_color=None,
        background_fill_color="#f0f0f0"
    )

    print(type(p.annular_wedge(
        x=0, 
        y=0,
        inner_radius='inner_radius',
        outer_radius='outer_radius',
        start_angle='start_angle',
        end_angle='end_angle',
        source=source,
        color="color",
        line_color='white',
        line_width=2
    )))


    p.text(
        x='text_x',
        y='text_y',
        text='name',           # Use the 'name' column for the text
        angle='text_angle',    # Rotate text to match the wedge angle
        source=source,
        text_align='center',
        text_baseline='middle',
        text_font_size='11px',
        text_color='text_color'
    )

    hover = HoverTool(tooltips=[("Name", "@name"), ("Count", "@value")])
    p.add_tools(hover)

    p.grid.grid_line_color = None

    show(p)
    return p


if __name__ == "__main__":
    from src.visualization.sunburst_server.hierarchical_data_counter import HierarchicalDataCounter
    hierarchies = [
        ['home', 'momir', 'repos'],
        ['home', 'momir',],
        ['home', 'lost+found',],
        ['var', 'log'],
        ['lib',],
    ]

    counter = HierarchicalDataCounter(hierarchies)
    df = counter.get_df()
    plot_sunburst(df, "File System Sunburst Chart")