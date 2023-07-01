import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mpc


class ScalarMappable(cm.ScalarMappable):
    def __init__(self, cmap, normalization, values, labels=None):
        cmap = self.get_cmap(cmap)
        norm = self.get_norm(normalization, values, cmap)
        super().__init__(norm, cmap)
        self._rnav_norm = normalization
        self._rnav_vals = values
        self._rnav_cmap = cmap
        self._rnav_labels = labels

    def __eq__(self, other):
        for prop in ['_rnav_norm', '_rnav_vals', '_rnav_cmap', '_rnav_labels']:
            if getattr(self, prop) != getattr(other, prop):
                return False
        else:
            return True

    def values_to_hexcolors(self, values, alpha=1.0):
        colors = super().to_rgba(x=values, alpha=alpha)
        return np.array([mpc.to_hex(c, keep_alpha=True) for c in colors])

    def get_norm(self, normalization, values, cmap):
        if normalization == 'min_max':
            return mpc.Normalize(values[0], values[1])
        elif normalization == '0_1':
            return mpc.Normalize()
        elif normalization == 'none':
            return mpc.NoNorm()
        elif normalization == 'bins':
            return mpc.BoundaryNorm(values, cmap.N, extend='both')

    def get_cmap(self, cmap):
        """Given a matplotlib color, list of colors, or colormap name, return
        a colormap object

        Args:
            cmap (str | tuple | float | list): A valid mpl color, list of valid
                colors or a valid colormap name

        Returns:
            matplotlib colormap: listed colormap matching the input
        """
        if mpc.is_color_like(cmap):
            return mpc.ListedColormap([cmap])
        elif (isinstance(cmap, list)
                and all(mpc.is_color_like(c) for c in cmap)):
            return mpc.ListedColormap(cmap)
        try:
            return cm.get_cmap(cmap)
        except ValueError as e:
            print("cmap must be one of: valid mpl color, list of mpl colors, or "
                f"mpl colormap:\n{str(cmap)}")
            raise e
