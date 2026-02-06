from . import pycorn
from . import graph
from . import pypage

def get_akta_data(path):
    """
    Load AKTA data from a zip file and return DataFrames and a plot.

    Args:
        path (str): Path to the UNICORN zip file.

    Returns:
        tuple: (akta_df, frac_df, phase_df, akta_fig)
    """
    akta_data = pycorn.load_uni_zip(path)

    akta_columns = list(akta_data.keys())

    use_akta_columns = [c for c in akta_columns if "UV" in c] + \
                       [ 'Cond', 'Conc B', 'pH'] + \
                       ['System flow', 'Sample flow'] + \
                       ['PreC pressure', 'System pressure', 'Sample pressure']

    hidden_columns =  ["Run Log",'Fractions','Injection']

    akta_df = pycorn.utils.get_series_from_data(akta_data, use_akta_columns + hidden_columns)
    frac_df = pycorn.utils.get_fraction_rectangle(akta_df)
    phase_df = pycorn.utils.find_phase(akta_df)

    akta_fig = graph.unicorn_ploty_graph(akta_df)
    akta_fig, _ = graph.annotate_fraction(akta_fig, frac_df, phase_df)

    return akta_df, frac_df, phase_df, akta_fig

def get_page_image(path, lane_width=44, margin=0.2):
    """
    Load a PAGE image and return a plotly figure for checking lanes.

    Args:
        path (str): Path to the image file.
        lane_width (int): Width of the lanes.
        margin (float): Margin between lanes.

    Returns:
        plotly.graph_objects.Figure: The annotated image figure.
    """
    page = pypage.PageImage(path, lane_width=lane_width, margin=margin)
    page_fig = page.check_image()
    return page_fig

def get_page_lane_ids(path, lane_width=44, margin=0.2):
    """
    Get the IDs (indices) of lanes in a PAGE image.

    Args:
        path (str): Path to the image file.
        lane_width (int): Width of the lanes.
        margin (float): Margin between lanes.

    Returns:
        list: List of lane indices.
    """
    page = pypage.PageImage(path, lane_width=lane_width, margin=margin)
    return list(range(len(page.lanes)))
