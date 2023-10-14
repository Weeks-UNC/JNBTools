import numpy as np
import matplotlib as mp
import matplotlib.patches as mp_patches
from rnavigate import styles

# 1-dimensional x-axis tracks
def plot_sequence_track(ax, sequence, yvalue=-0.05, height=0.05, ytrans="data",
        verticalalignment='bottom', region="all"):
    style = styles.settings['sequence_bar']
    ymin, ymax = ax.get_ylim()
    if ytrans == "axes":
        yvalue = (ymax - ymin) * yvalue + ymin
        height = (ymax - ymin) * height
    if region == "all":
        region = [1, len(sequence)]
    sequence = sequence[region[0] - 1 : region[1]]
    if style == 'alphabet':
        for i, nt in enumerate(sequence):
            # set font style and colors for each nucleotide
            font_prop = mp.font_manager.FontProperties(
                family="monospace", style="normal", weight="bold", size="4")
            col = styles.get_nt_color(nt)
            ax.text(
                i + region[0], yvalue, nt, fontproperties=font_prop, color=col,
                horizontalalignment="center",
                verticalalignment=verticalalignment
                )
    if style == 'bars':
        sequence = list(sequence)
        colors = [styles.get_nt_color(nt) for nt in sequence]
        is_uppercase = np.char.isupper(sequence)
        heights = np.full(len(sequence), height/2)
        heights *= (is_uppercase + 1)
        heights *= np.char.not_equal(sequence, '-')
        if verticalalignment == 'top':
            heights *= -1
        x = np.arange(region[0], region[1]+1)
        ax.bar(
            x, heights, bottom=yvalue, width=1, color=colors, ec='none',
            clip_on=False
            )
    ax.set_ylim(ymin, ymax)


def plot_annotation_track(
        ax, annotation, yvalue, mode, region='all', ytrans='data'
        ):
    if region == 'all':
        region = [1, annotation.length]
    mn, mx = region
    if ytrans == "axes":
        ymin, ymax = ax.get_ylim()
        yvalue = (ymax - ymin) * yvalue + ymin
    color = annotation.color
    modes = ["track", "bar"]
    
    def plot_track(*s, alpha=1):
        start, end = min(s)-0.5, max(s)+0.5
        if mode == "track":
            ax.plot(
                [start, end], [yvalue]*2, color=color, alpha=alpha, lw=5,
                solid_capstyle='butt', clip_on=False,
                )
        elif mode == 'bar' and len(s) == 2:
            ax.axvspan(start-0.5, end+0.5, fc=color, ec="none", alpha=0.1)
        elif mode == 'bar' and len(s) == 1:
            print(start)
            ax.axvline(start+0.5, color=color, ls=":")

    assert mode in modes, f"annotation mode must be one of: {modes}"
    a_type = annotation.annotation_type
    if a_type == "spans" or (a_type == "primers" and mode == "bar"):
        for start, end in annotation:
            plot_track(start, end)
    elif a_type == "sites":
        for site in annotation.data['site']:
            plot_track(site)
    elif a_type == "group":
        sites = annotation.data['site']
        plot_track(min(sites), max(sites), alpha=0.5)
        for site in sites:
            plot_track(site)
    elif a_type == "primers":
        for start, end in annotation:
            if start > end:
                start, end = start + 0.5, end - 0.5
            else:
                start, end = start - 0.5, end + 0.5
            ax.arrow(
                x=start, y=yvalue, dx=end-start+1, dy=0, color=color,
                shape='right', clip_on=False, head_width=0.01, head_length=3,
                length_includes_head=True,
                )


def plot_domain_track(ax, spans, yvalue, height, region='all', ytrans="data"):
    if region == 'all':
        region = [1, spans.length]
    mn, mx = region
    text_height=height
    if ytrans == "axes":
        ymin, ymax = ax.get_ylim()
        yvalue = (ymax - ymin) * yvalue + ymin
        height = (ymax - ymin) * height
        text_height = 6
    name = spans.name
    color = spans.color
    for start, end in spans:
        start = max([mn, start])
        end = min([mx, end])
        rect = mp_patches.Rectangle(
            xy=(start-0.5, yvalue), width=end-start+1, height=height,
            linewidth=1, edgecolor='black', facecolor=color, clip_on=False,
            )
        ax.add_patch(rect)
        ax.text(
            x=(end-start)/2 + start, y=yvalue+height/2, s=name, zorder=25,
            horizontalalignment='center', verticalalignment='center',
            fontdict={'size': text_height*1.5}, clip_on=False,
            )
