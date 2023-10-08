from functools import wraps
import matplotlib as mpl
import seaborn as sns
from rnavigate import data

# STYLE SHEET
###############################################################################

settings = {
    'sequence_bar': 'alphabet', # 'bars'
    'sequence_colors': 'rnavigate', # 'old'
    'ss': {
        'structure': {
            'linewidth': 1,
            'zorder': 2},
        'points': {
            's': 3**2,
            'zorder': 2},
        'interactions': {
            'linewidth': 3,
            'alpha': None,
            'zorder': 15},
        'spans': {
            'linewidth': 10,
            'alpha': 0.4,
            'zorder': 5},
        'sites': {
            'marker': 'o',
            'edgecolor': 'none',
            's': 10**2,
            'alpha': 0.4,
            'zorder': 5},
        'basepairs': {
            'zorder': 0},
        'nucleotides': {
            'marker': 'o',
            's': 5**2,
            'zorder': 10},
        'sequence': {
            'linewidth': 0.3,
            's': 3**2,
            'zorder': 20},
        'positions': {
            'zorder': 25},
    },
}

def set_defaults():
    sns.set_context("paper")
    sns.set_style("ticks")
    colors = [
        '#0092edff',  # Blue
        '#ff8300ff',  # Orange
        '#a100ffff',  # Purple
        '#edc600ff',  # Yellow
        '#ff48e9ff',  # Pink
        '#3fd125ff'  # Green
    ]
    sns.set_palette(colors)
    mpl.rcParams["font.sans-serif"].insert(0, "Arial")
    mpl.rcParams['figure.dpi'] = 140
    mpl.rcParams["svg.fonttype"] = 'none'


def get_nt_color(nt, colors=None):
    if colors is None:
        colors = settings['sequence_colors']
    try:
        return {"old": {"A": "#f20000",  # red
                        "U": "#f28f00",  # yellow
                        "G": "#00509d",  # blue
                        "C": "#00c200"},  # green
                "rnavigate": {"A": "#366ef0",  # blue
                              "U": "#9bb9ff",  # light blue
                              "G": "#f04c4c",  # red
                              "C": "#ffa77c"}  # light red
                }[colors][nt.upper().replace("T", "U")]
    except KeyError:
        return "#aaaaaa"

def get_nt_cmap():
    return data.ScalarMappable(
        cmap=[get_nt_color(nt) for nt in 'AUGC'],
        normalization='none', values=None, title="sequence",
        tick_labels=['A', 'U', 'G', 'C'])

def apply_style(style_dict):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            with mpl.rc_context(style_dict):
                return function(*args, **kwargs)
        return wrapper
    return decorator


# ShapeMapper Plot Styles
sm = {"font.family": "sans-serif",
      "pdf.fonttype": 42,
      # use TrueType fonts when exporting PDFs
      # (embeds most fonts - this is especially
      #  useful when opening in Adobe Illustrator)
      'xtick.direction': 'out',
      'ytick.direction': 'out',
      'legend.fontsize': 14,
      'grid.color': ".8",
      'grid.linestyle': '-',
      'grid.linewidth': 1}

rx_color = "red"
bg_color = "blue"
dc_color = "darkgoldenrod"


# set default styles for plotting
set_defaults()
