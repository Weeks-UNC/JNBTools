import numpy as np
import matplotlib.patches as mp_patches
import matplotlib.collections as mp_collections
import matplotlib.colors as mp_colors
from rnavigate import data, plots


def get_contrasting_colors(colors):
    contrasting = ["k"] * len(colors)
    for i, color in enumerate(colors):
        r, g, b = mp_colors.to_rgb(color)
        if (r * 0.299 + g * 0.587 + b * 0.114) < 175 / 256:
            contrasting[i] = "w"
    return np.array(contrasting)


def adjust_spines(ax, spines):
    for loc, spine in ax.spines.items():
        if loc in spines:
            spine.set_position(("outward", 10))  # outward by 10 points
        else:
            spine.set_color("none")  # don't draw spine
    if "left" in spines:
        ax.yaxis.set_ticks_position("left")
    else:
        ax.yaxis.set_ticks([])
    if "bottom" in spines:
        ax.xaxis.set_ticks_position("bottom")
    else:
        ax.xaxis.set_ticks([])


def clip_spines(ax, spines):
    for spine in spines:
        if spine in ["left", "right"]:
            ticks = ax.get_yticks()
        if spine in ["top", "bottom"]:
            ticks = ax.get_xticks()
        ax.spines[spine].set_bounds((min(ticks), max(ticks)))


def get_nt_ticks(sequence, region, gap):
    if isinstance(sequence, data.Sequence):
        sequence = sequence.sequence
    start, end = region
    labels = []
    ticks = []
    pos = 0
    for i, nt in enumerate(sequence):
        valid = nt != "-"
        if valid:
            pos += 1
        if valid & (pos % gap == 0 or pos == start) and start <= pos <= end:
            labels.append(pos)
            ticks.append(i + 1)
    return ticks, labels


def set_nt_ticks(ax, sequence, region, major, minor):
    ticks, labels = get_nt_ticks(sequence, region, major)
    ax.set_xticks(ticks=ticks)
    ax.set_xticklabels(labels=labels)
    ax.set_xticks(minor=True, ticks=get_nt_ticks(sequence, region, minor)[0])


def box_xtick_labels(ax):
    for label in ax.get_xticklabels():
        label.set_bbox(
            {
                "facecolor": "white",
                "edgecolor": "None",
                "alpha": 0.5,
                "boxstyle": "round,pad=0.1,rounding_size=0.2",
            }
        )


def plot_sequence_alignment(ax, alignment, labels, top=5, bottom=-5, ytrans="data"):
    al1 = alignment.alignment1
    al2 = alignment.alignment2
    height = (top - bottom) / 3
    plots.plot_sequence_track(
        ax, sequence=al1, yvalue=bottom, height=height, ytrans=ytrans
    )
    plots.plot_sequence_track(
        ax,
        sequence=al2,
        yvalue=top,
        height=height,
        ytrans=ytrans,
        verticalalignment="top",
    )
    set_nt_ticks(ax=ax, sequence=al1, region=(1, len(al1)), major=20, minor=5)
    ax.set_xlabel(labels[0], loc="left")
    ax.spines["bottom"].set(position=(ytrans, bottom), visible=False)
    ax2 = ax.twiny()
    ax2.set(xlim=ax.get_xlim())
    ax2.spines["top"].set(position=(ytrans, top), visible=False)
    set_nt_ticks(ax=ax2, sequence=al2, region=(1, len(al2)), major=20, minor=5)
    ax2.set_xlabel(labels[1], loc="left")

    for spine in ["top", "bottom", "left", "right"]:
        ax2.spines[spine].set_visible(False)
    for spine in ["top", "bottom", "left", "right"]:
        ax.spines[spine].set_visible(False)

    for idx, (nt1, nt2) in enumerate(zip(al1, al2)):
        if nt1.upper().replace("T", "U") == nt2.upper().replace("T", "U"):
            ax.fill_between(
                x=[idx + 0.5, idx + 1.5],
                y1=bottom + height,
                y2=top - height,
                color="grey",
                ec="none",
            )


def plot_interactions_arcs(ax, interactions, panel, yvalue=0, region="all"):
    if region == "all":
        region = [1, interactions.length]
    mn, mx = region
    ij_colors = interactions.get_ij_colors()
    patch_list = []
    for i, j, color in zip(*ij_colors):
        if j < i:  # flip the order
            i, j = j, i
        if not (mn < i < mx) and not (mn < j < mx):
            continue
        center = ((i + j) / 2.0, yvalue)
        if panel == "top":
            theta1, theta2 = 0, 180
        elif panel == "bottom":
            theta1, theta2 = 180, 360
        radius = 0.5 + (j - i) / 2.0
        patch_list.append(
            mp_patches.Wedge(
                center, radius, theta1, theta2, color=color, width=1, ec="none"
            )
        )
    ax.add_collection(mp_collections.PatchCollection(patch_list, match_original=True))


def plot_profile_bars(
    ax, profile, scale_factor=1, plot_error=True, bottom=0, region="all"
):
    if region == "all":
        region = [1, profile.length]
    mn, mx = region
    data = profile.get_plotting_dataframe()
    values = data["Values"]
    colormap = data["Colors"]
    nts = data["Nucleotide"]
    if plot_error and ("Errors" in data.columns):
        yerr = data["Errors"] * scale_factor
        ax.bar(
            nts[mn - 1 : mx],
            values[mn - 1 : mx] * scale_factor,
            align="center",
            bottom=bottom,
            width=1,
            color=colormap[mn - 1 : mx],
            edgecolor=colormap[mn - 1 : mx],
            linewidth=0.0,
            yerr=yerr[mn - 1 : mx],
            ecolor=(0, 0, 1 / 255.0),
            capsize=0,
        )
    else:
        ax.bar(
            nts[mn - 1 : mx],
            values[mn - 1 : mx] * scale_factor,
            align="center",
            width=1,
            color=colormap[mn - 1 : mx],
            bottom=bottom,
            edgecolor=colormap[mn - 1 : mx],
            linewidth=0.0,
        )


def plot_profile_skyline(ax, profile, label, columns, errors):
    values = profile.data
    if columns is None:
        columns = profile.metric
    if isinstance(columns, str) and isinstance(errors, (str, type(None))):
        columns = [columns]
        errors = [errors]
    if errors is None:
        errors = [None] * len(columns)
    if len(errors) != len(columns):
        raise ValueError("columns and errors lists must be the same length")
    for column, error in zip(columns, errors):
        lines = ax.plot(
            values["Nucleotide"],
            values[column],
            drawstyle="steps-mid",
            label=f"{label}: {column.replace('_', ' ')}",
        )
        if error is not None:
            ax.fill_between(
                values["Nucleotide"],
                values[column] - values[error],
                values[column] - values[error],
                step="mid",
                color=lines[0].get_color(),
                alpha=0.25,
                lw=0,
            )
