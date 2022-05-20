import numpy as np
from .plots import Plot
from matplotlib.patches import Rectangle
from ..styles import rx_color, bg_color, dc_color, apply_style, sm


class SM(Plot):
    def __init__(self, nt_length, plots=["profile", "rates", "depth"]):
        self.nt_length = nt_length
        super().__init__(len(plots), len(plots), cols=1)
        self.plots = plots

    def get_figsize(self):
        left_inches = 0.9
        right_inches = 0.4
        ax_width = self.nt_length * 0.1
        fig_height = 6
        fig_width = max(7, ax_width + left_inches + right_inches)
        return (fig_width*self.columns, fig_height*self.rows)

    @apply_style(sm)
    def plot_data(self, profile, label):
        """Creates a figure with the three classic Shapemapper plots.
        """
        self.fig.suptitle(label, fontsize=30)
        for i, plot in enumerate(self.plots):
            ax = self.get_ax(i)
            plot_func = {"profile": self.plot_sm_profile,
                         "rates": self.plot_sm_rates,
                         "depth": self.plot_sm_depth
                         }[plot]
            plot_func(ax, profile)

    def plot_sm_profile(self, ax, profile):
        """Plots classic ShapeMapper normalized reactivity on the given axis

        Args:
            axis (pyplot axis): axis on which to add plot
        """
        yMin, ymax = (-0.5, 4)
        near_black = (0, 0, 1 / 255.0)
        orange_thresh = 0.4
        red_thresh = 0.85
        colors = profile.get_colors("profile", profile=profile)
        sample = profile.data["Norm_profile"].copy()
        sample[np.isnan(sample)] = -1
        ax.bar(profile.data['Nucleotide'], sample, align="center",
               width=1.05, color=colors, edgecolor=colors,
               linewidth=0.0, yerr=profile.data['Norm_stderr'],
               ecolor=near_black, capsize=1)
        ax.set_title("Normalized Profile", fontsize=16)
        ax.set_ylim(yMin, ymax)
        ax.set_xlim(1, profile.length)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.set_xlabel("Nucleotide", fontsize=14, labelpad=0)
        ax.set_ylabel("Shape Reactivity", fontsize=14)
        # add a SHAPE colorbar to the vertical ax
        # uses a little transformation magic to place correctly
        inv = ax.transData.inverted()
        for loc, spine in list(ax.spines.items()):
            if loc == 'left':
                trans = spine.get_transform()
        tp = trans.transform_point([0, 0])
        tp2 = inv.transform_point(tp)
        rectX = tp2[0]
        tpA = (0, 0)
        tpB = (6, 0)
        tpA2 = inv.transform_point(tpA)
        tpB2 = inv.transform_point(tpB)
        rectW = tpB2[0] - tpA2[0]
        rect = Rectangle((rectX, -0.5), rectW, orange_thresh +
                         0.5, facecolor="black", edgecolor="none")
        ax.add_patch(rect)
        rect.set_clip_on(False)
        rect = Rectangle((rectX, orange_thresh), rectW, red_thresh -
                         orange_thresh, facecolor="orange", edgecolor="none")
        ax.add_patch(rect)
        rect.set_clip_on(False)
        rect = Rectangle((rectX, red_thresh), rectW, 4 -
                         red_thresh, facecolor="red", edgecolor="none")
        ax.add_patch(rect)
        rect.set_clip_on(False)
        ax.get_xaxis().tick_bottom()   # remove unneeded ticks
        ax.get_yaxis().tick_left()
        ax.tick_params(axis='y', which='minor', left=False)
        ax.minorticks_on()

        yticks = ax.get_yticks()
        stripped_ticks = [str(int(val)) for val in yticks]
        ax.set(yticks=yticks,
               yticklabels=stripped_ticks)

        for line in ax.get_yticklines():
            line.set_markersize(6)
            line.set_markeredgewidth(1)

        for line in ax.get_xticklines():
            line.set_markersize(7)
            line.set_markeredgewidth(2)

        for line in ax.xaxis.get_ticklines(minor=True):
            line.set_markersize(5)
            line.set_markeredgewidth(1)

        # put nuc sequence below axis
        self.add_sequence(ax, profile.sequence)

    def plot_sm_depth(self, ax, profile):
        """Plots classic ShapeMapper read depth on the given axis

        Args:
            axis (pyplot axis): axis on which to add plot
        """
        sample = profile.data
        ax.plot(sample['Nucleotide'], sample['Modified_read_depth'],
                linewidth=1.5, color=rx_color, alpha=1.0, label="Modified")
        ax.plot(sample['Nucleotide'], sample['Untreated_read_depth'],
                linewidth=1.5, color=bg_color, alpha=1.0, label="Untreated")
        ax.plot(sample['Nucleotide'], sample['Denatured_read_depth'],
                linewidth=1.5, color=dc_color, alpha=1.0, label="Denatured")
        ax.set_xlim(1, profile.length)
        ax.legend(loc=2, borderpad=0.8, handletextpad=0.2, framealpha=0.75)
        ax.plot(sample['Nucleotide'], sample['Modified_effective_depth'],
                linewidth=1.0, color=rx_color, alpha=0.3)
        ax.plot(sample['Nucleotide'], sample['Untreated_effective_depth'],
                linewidth=1.0, color=bg_color, alpha=0.3)
        ax.plot(sample['Nucleotide'], sample['Denatured_effective_depth'],
                linewidth=1.0, color=dc_color, alpha=0.3)
        xmin, xmax, ymin, ymax = ax.axis()
        ax.set_ylim(0, ymax)
        ax.set_xlabel("Nucleotide\n" +
                      "NOTE: effective read depths shown in lighter colors",
                      fontsize=14, labelpad=0)
        ax.minorticks_on()
        ax.tick_params(axis='y', which='minor', left=False)
        yticks = [int(y) for y in ax.get_yticks()]
        formatted_ticks = [self.metric_abbreviate(val) for val in yticks]
        ax.set(yticks=yticks, yticklabels=formatted_ticks)
        for line in ax.get_yticklines():
            line.set_markersize(6)
            line.set_markeredgewidth(1)
        for line in ax.get_xticklines():
            line.set_markersize(7)
            line.set_markeredgewidth(2)
        for line in ax.xaxis.get_ticklines(minor=True):
            line.set_markersize(5)
            line.set_markeredgewidth(1)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.set_ylabel("Read depth", fontsize=14)
        # tried to make an offset, smaller font note about effective depths,
        # but couldn't get positioning/transforms to work properly.
        # For now just putting in xaxis label

    def plot_sm_rates(self, ax, profile):
        """Plots classic ShapeMapper mutation rates on the given axis

        Args:
            axis (pyplot axis): axis on which to add plot
        """
        sample = profile.data
        # choose a decent range for ax, excluding high-background positions
        temp_rates = sample.loc[sample['Untreated_rate'] <= 0.05,
                                'Modified_rate']
        near_top_rate = np.nanpercentile(temp_rates, 98.0)
        maxes = np.array([0.32, 0.16, 0.08, 0.04, 0.02, 0.01])
        ymax = np.amin(maxes[maxes > near_top_rate])
        rx_err = sample['Modified_rate'] / sample['Modified_effective_depth']
        rx_upper = sample['Modified_rate'] + rx_err
        rx_lower = sample['Modified_rate'] - rx_err
        bg_err = sample['Untreated_rate'] / sample['Untreated_effective_depth']
        bg_upper = sample['Untreated_rate'] + bg_err
        bg_lower = sample['Untreated_rate'] - bg_err
        dc_err = sample['Denatured_rate'] / sample['Denatured_effective_depth']
        dc_upper = sample['Denatured_rate'] + dc_err
        dc_lower = sample['Denatured_rate'] - dc_err
        ax.set_xlabel("Nucleotide", fontsize=14)
        ax.set_ylabel("Mutation rate (%)", fontsize=14)
        ax.plot(sample['Nucleotide'], sample['Modified_rate'], zorder=3,
                color=rx_color, linewidth=1.5, label='Modified')
        ax.plot(sample['Nucleotide'], sample['Untreated_rate'], zorder=2,
                color=bg_color, linewidth=1.5, label='Untreated')
        ax.plot(sample['Nucleotide'], sample['Denatured_rate'], zorder=2,
                color=dc_color, linewidth=1.5)
        ax.fill_between(sample['Nucleotide'], rx_lower, rx_upper,
                        edgecolor="none", alpha=0.5, facecolor=rx_color)
        ax.fill_between(sample['Nucleotide'], bg_lower, bg_upper,
                        edgecolor="none", alpha=0.5, facecolor=bg_color)
        ax.fill_between(sample['Nucleotide'], dc_lower, dc_upper,
                        edgecolor="none", alpha=0.5, facecolor=dc_color)
        ax.legend(loc=2, borderpad=0.8, handletextpad=0.2, framealpha=0.75)
        ax.set_xlim((1, len(sample['Modified_rate'])))
        ax.set_ylim((0, ymax))
        ax.minorticks_on()
        ax.tick_params(axis='y', which='minor', left=False)
        yticks = ax.get_yticks()
        yticklabels = [str(int(x*100)) for x in yticks]
        ax.set(yticks=yticks, yticklabels=yticklabels)
        for line in ax.get_yticklines():
            line.set_markersize(6)
            line.set_markeredgewidth(1)
        for line in ax.get_xticklines():
            line.set_markersize(7)
            line.set_markeredgewidth(2)
        for line in ax.xaxis.get_ticklines(minor=True):
            line.set_markersize(5)
            line.set_markeredgewidth(1)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)

    def metric_abbreviate(self, num):
        """takes a large number and applies an appropriate abbreviation

        Args:
            num (int): number to be abbreviated

        Returns:
            str: abbreviated number
        """
        suffixes = {3: 'k',
                    6: 'M',
                    9: "G"}
        s = str(num)
        # replace trailing zeros with metric abbreviation
        zero_count = len(s) - len(s.rstrip('0'))
        suffix = ''
        new_string = str(s)
        for num_zeros in sorted(suffixes.keys()):
            if num_zeros <= zero_count:
                suffix = suffixes[num_zeros]
                new_string = s[:-num_zeros]
                new_string = new_string + suffix
        return new_string
