import pandas as pd
import numpy as np
from rnavigate import data
from types import FunctionType


class Profile(data.Data):
    def __init__(self, input_data, metric='default', metric_defaults=None,
                 read_table_kw=None, sequence=None):
        if metric_defaults is None:
            metric_defaults = {}
        super().__init__(
            input_data=input_data,
            sequence=sequence,
            metric=metric,
            metric_defaults=metric_defaults,
            read_table_kw=read_table_kw)

    @property
    def recreation_kwargs(self):
        return {}

    def normalize_sequence(self, t_or_u='U', uppercase=True):
        super().normalize_sequence(
            t_or_u=t_or_u,
            uppercase=uppercase)
        self.data["Sequence"] = list(self.sequence)

    def get_aligned_data(self, alignment):
        dataframe = alignment.map_nucleotide_dataframe(self.data)
        return self.__class__(
            input_data=dataframe,
            metric=self._metric,
            metric_defaults=self.metric_defaults,
            sequence=alignment.target_sequence,
            **self.recreation_kwargs)

    def get_plotting_dataframe(self):
        new_names = ["Nucleotide"]
        old_names = ["Nucleotide"]
        old_names.append(self.metric)
        new_names.append("Values")
        if self.error_column is not None:
            old_names.append(self.error_column)
            new_names.append("Errors")
        plotting_dataframe = self.data[old_names].copy()
        plotting_dataframe.columns = new_names
        plotting_dataframe["Colors"] = self.colors
        return plotting_dataframe

    def calculate_windows(
            self, column, window, method='median', new_name=None,
            minimum_points=None, mask_na=True,
            ):
        """calculates a windowed operation over a column of self.data and
        stores the result as a new column. Value of each window is assigned to
        the center position of the window.

        Args:
            column (str): name of column to perform operation on
            window (int): window size, must be an odd number
            method (str, optional): operation to perform over windows, must be
                one of 'median', 'mean', 'minimum', 'maximum'
                Defaults to 'median'.
            new_name (str, optional): name of new column for stored result.
                Defaults to f"{method}_{window}_nt", e.g. "median_55_nt".
            minimum_points (int, optional): minimum number of points within
                each window.
                Defaults to the size of the window.
        """
        if window % 2 != 1:
            raise ValueError('`window` argument must be an odd number.')
        if new_name is None:
            new_name = f'{method}_{window}_nt'
        if minimum_points is None:
            minimum_points = window
        windows = self.data[column].rolling(
            window=window, center=True, min_periods=minimum_points)
        if method == 'median':
            self.data[new_name] = windows.median()
        elif method == 'mean':
            self.data[new_name] = windows.mean()
        elif method == 'minimum':
            self.data[new_name] = windows.min()
        elif method == 'maximum':
            self.data[new_name] = windows.max()
        elif isinstance(method, FunctionType):
            self.data[new_name] = windows.apply(method)
        else:
            raise ValueError(
                'method argument must be median, mean, maximum or minimum'
                )
        if mask_na:
            self.data.loc[self.data[column].isna(), new_name] = np.nan

    def calculate_gini_index(self, values):
        """Calculate the Gini index of an array of values."""
        # Mean absolute difference
        mad = np.abs(np.subtract.outer(values, values)).mean()
        # Relative mean absolute difference
        rmad = mad/np.mean(values)
        # Gini coefficient
        g = 0.5 * rmad
        return g

    def normalize(
            self, profile_column=None, new_profile=None, error_column=None,
            new_error=None, norm_method=None, nt_groups=None,
            profile_factors=None, **norm_kwargs
            ):
        """normalize the values in the given values and errors columns. Stores
        values in column of self.data dataframe.

        Args:
            profile_column (str, optional): column name of values to normalize
                Defaults to self.metric
            new_profile (str, optional): column name of new normalized values
                Defaults to "Norm_profile"
            error_column (str, optional): column name of error values to propagate
                Defaults to self.error_column
            new_error (str, optional): column name of new propagated error values
                Defaults to "Norm_error"
            norm_method (str, optional): normalization method to use.
                "DMS" uses self.norm_percentile and nt_groups=['AC', 'UG']
                    scales the median of 90th to 95th percentiles to 1
                    As and Cs are normalized seperately from Us and Gs
                "eDMS" uses self.norm_eDMS and  nt_groups=['A', 'U', 'C', 'G']
                    Applies the new eDMS-MaP normalization.
                    Each nucleotide is normalized seperately.
                "boxplot" uses self.norm_boxplot and nt_groups=['AUCG']
                    removes outliers (> 1.5 iqr) and scales median to 1
                    scales nucleotides together unless specified with nt_groups
                "percentile" uses self.norm_percentile and nt_groups=['AUCG']
                    scales the median of 90th to 95th percentiles to 1
                    scales nucleotides together unless specified with nt_groups
                Defaults to "boxplot": the default normalization of ShapeMapper
            nt_groups (list of str, optional): A list of nucleotides to group
                e.g. ['AUCG'] groups all nts together
                     ['AC', 'UG'] groups As with Cs and Us with Gs
                     ['A', 'C', 'U', 'G'] scales each nt seperately
                     Default depends on norm_method
            profile_factors (dict, optional): a scaling factor (float) for each
                nucleotide: keys must be 'A', 'C', 'U', 'G'
                Note: using this argument overrides any calculation of scaling
                Defaults to None.
            **norm_kwargs: these are passed to the norm_method function

        Returns:
            dict: the new profile scaling factors dictionary
        """
        if profile_column is None:
            profile_column = self.metric
        if new_profile is None:
            new_profile = "Norm_profile"
        if error_column is None:
            error_column = self.error_column
        if new_error is None:
            new_error = "Norm_error"
        profile = self.data[profile_column]
        norm_sequence = self.sequence.upper().replace('T', 'U')
        # initialize the error arrays
        if error_column is not None:
            error = self.data[error_column]
            normerr = np.zeros(error.shape)
            mask = profile != 0
            normerr[mask] = (error[mask]/profile[mask])**2
        else:
            normerr = None
        # calculate normalization factors, if appropriate
        if profile_factors is None:
            profile_factors = {nt: np.nan for nt in 'ACGU'}
            error_factors = {}
            methods_groups = {
                'DMS': (self.norm_percentiles, ['AC', 'GU']),
                'eDMS': (self.norm_eDMS, ['A', 'C', 'G', 'U']),
                'boxplot': (self.norm_boxplot, nt_groups),
                'percentiles': (self.norm_percentiles, nt_groups)
            }
            norm_method, nt_groups = methods_groups[norm_method]
            if nt_groups is None:
                nt_groups = ['AUCG']
            for nt_group in nt_groups:
                in_group = [nt in nt_group for nt in norm_sequence]
                prof, err = norm_method(profile[in_group], **norm_kwargs)
                for nt in nt_group:
                    profile_factors[nt] = prof
                    error_factors[nt] = err
        # calculate the new profile
        norm_profile = profile / [profile_factors[nt] for nt in norm_sequence]
        self.data[new_profile] = norm_profile
        # calculate the new errors, if appropriate
        if normerr is not None and error_factors is not None:
            for i in 'AUCG':
                mask = [nt == i for nt in norm_sequence]
                normerr[mask] += (error_factors[i] * profile_factors[i])**2
                normerr[mask] = np.sqrt(normerr[mask])
                normerr[mask] *= np.abs(norm_profile[mask])
            self.data[new_error] = normerr
        return profile_factors

    def normalize_external(self, profiles, **kwargs):
        """normalize reactivities using other profiles to normfactors.

        Args:
            profiles (list of rnavigate.data.Profile): a list of other profiles
                used to compute scaling factors

        Returns:
            dict: the new profile scaling factors dictionary
        """
        combined_df = pd.concat([profile.data for profile in profiles])
        combined_profile = Profile(input_data=combined_df)
        nfacs = combined_profile.normalize(**kwargs)
        self.normalize(profile_factors=nfacs)
        return nfacs

    def norm_boxplot(self, values):
        """removes outliers (> 1.5 * IQR) and scales the mean to 1.

        NOTE: This method varies slightly from normalization method used in the
        SHAPEMapper pipeline. Shapemapper sets undefined values to 0, and then
        uses these values when computing iqr and 90th percentile. Including
        these values can skew these result. This method excludes such nan
        values. Other elements are the same.

        Args:
            values (1D numpy array): values to scale

        Returns:
            (float, float): scaling factor and error propagation factor
        """
        finite_values = values[np.isfinite(values)]
        p25, p75, p90, p95 = np.percentile(finite_values, [25, 75, 90, 95])
        iqr = p75 - p25
        # filter by iqr
        iqr_values = finite_values[finite_values < (1.5 * iqr + p75)]
        num_finite = len(finite_values)
        num_iqr = len(iqr_values)
        # see if too many values are classified as outliers
        if num_finite < 100 and num_iqr/num_finite < 0.95:
            iqr_values = finite_values[finite_values <= p95]
        elif num_finite >= 100 and num_iqr/num_finite < 0.9:
            iqr_values = finite_values[finite_values < p90]
        new_p90 = np.percentile(iqr_values, 90)
        final_values = iqr_values[iqr_values > new_p90]
        factor = np.mean(final_values)
        error_factor = np.std(final_values) / np.sqrt(len(final_values))
        return factor, error_factor

    def norm_eDMS(self, values):
        """Returns normalization factors for normalize values following eDMS
        pernt scheme in ShapeMapper 2.2

        Args:
            values (1D numpy array): values to scale

        Returns:
            (float, float): scaling factor and error propagation factor
        """
        # if too few values points, don't normalize
        if len(values)<10:
            return np.nan, np.nan
        bounds = np.percentile(values, [90., 95.])
        mask = (values >= bounds[0]) & (values<bounds[1])
        normset = values[mask]
        # compute the norm the standard way
        n1 = np.mean(normset)
        try:
            # compute the norm only considering reactive nts
            n2 = np.percentile(values[values>0.001], 75.)
        except IndexError:
            n2 = 0
        factor = max(n1,n2)
        # if signal too low, don't norm the values
        if factor < 0.002:
            return np.nan, np.nan
        error_factor = np.std(normset) / np.sqrt(len(normset))
        return factor, error_factor

    def norm_percentiles(self, values, lower_bound=90, upper_bound=99):
        """Calculates profile scaling factors and error propagation by scaling
        the median between upper and lower bound percentiles to 1.

        Args:
            values (1D numpy.array): values to scale
            lower_bound (int or float, optional): percentile of lower bound
                Defaults to 90
            upper_bound (int or float, optional): percentile of upper bound
                Defaults to 99

        Returns:
            (float, float): scaling factor and error propagation factor
        """
        finite_values = values[np.isfinite(values)]
        bounds = np.percentile(finite_values, [lower_bound, upper_bound])
        mask = (finite_values >= bounds[0]) & (finite_values <= bounds[1])
        normset = finite_values[mask]
        factor = np.mean(normset)
        error_factor = np.std(normset) / np.sqrt(len(normset))
        return factor, error_factor


class SHAPEMaP(Profile):
    def __init__(
            self, input_data, normalize=None, read_table_kw=None,
            sequence=None, metric='Norm_profile', metric_defaults=None,
            log=None,
            ):
        self.read_lengths, self.mutations_per_molecule = self.read_log(log)
        if metric_defaults is None:
            metric_defaults = {}
        metric_defaults = {
            'Norm_profile': {
                'metric_column': 'Norm_profile',
                'error_column': 'Norm_stderr',
                'cmap': ["grey", "black", "orange", "red", "red"],
                'normalization': "bins",
                'values': [-0.4, 0.4, 0.85, 2],
                'title': 'SHAPE Reactivity',
                'extend': 'both'}
            } | metric_defaults
        if (isinstance(input_data, str)
                and input_data.endswith(".map")
                and read_table_kw is None):
            read_table_kw = {
                "names": ["Nucleotide", "Norm_profile",
                          "Norm_stderr", "Sequence"],
                "na_values": "-999"}

        super().__init__(input_data=input_data,
                         read_table_kw=read_table_kw,
                         sequence=sequence,
                         metric=metric,
                         metric_defaults=metric_defaults)
        if normalize is not None:
            self.normalize(
                profile_column="HQ_profile", new_profile="Norm_profile",
                error_column="HQ_stderr", new_error="Norm_stderr",
                norm_method=normalize,
                )

    def read_log(self, log):
        if log is None:
            return None, None
        with open(log, 'r') as f:
            flist = list(f)
            log_format_test = 0
            for i, line in enumerate(flist):
                if line.startswith("  |MutationCounter_Modified"):
                    log_format_test += 1
                    modlength = []
                    for x in flist[i+6:i+27]:
                        modlength.append(float(x.strip().split('\t')[1]))
                    modmuts = []
                    for x in flist[i+32:i+53]:
                        modmuts.append(float(x.strip().split('\t')[1]))
                if line.startswith("  |MutationCounter_Untreated"):
                    log_format_test += 1
                    untlength = []
                    for x in flist[i+6:i+27]:
                        untlength.append(float(x.strip().split('\t')[1]))
                    untmuts = []
                    for x in flist[i+32:i+53]:
                        untmuts.append(float(x.strip().split('\t')[1]))
        message = ("Histogram data missing from log file. Requires" +
                   " --per-read-histogram flag when running ShapeMapper.")
        assert log_format_test >= 2, message
        read_lengths = pd.DataFrame({
            'Read_length': [
                '0-49', '50-99', '100-149', '150-199', '200-249', '250-299',
                '300-349', '350-399', '400-449', '450-499', '500-549',
                '550-599', '600-649', '650-699', '700-749', '750-799',
                '800-849', '850-899', '900-949', '950-999', '>1000'
                ],
            'Modified_read_length': modlength,
            'Untreated_read_length': untlength,
            })
        mutations_per_molecule = pd.DataFrame({
                'Mutation_count': np.arange(21),
                'Modified_mutations_per_molecule': modmuts,
                'Untreated_mutations_per_molecule': untmuts
            })
        return read_lengths, mutations_per_molecule


class DanceMaP(SHAPEMaP):
    def __init__(self, input_data, component, read_table_kw=None,
                 sequence=None, metric='Norm_profile', metric_defaults=None):
        self.component = component
        super().__init__(input_data=input_data,
                         read_table_kw=read_table_kw,
                         sequence=sequence,
                         metric=metric,
                         metric_defaults=metric_defaults)

    @property
    def recreation_kwargs(self):
        return {'component': self.component}


    def read_file(self, input_data, read_table_kw={}):
        # parse header
        self.filepath = input_data
        with open(self.filepath) as f:
            header1 = f.readline()
            header2 = f.readline()
        self.header = header1 + header2
        self.components = int(header1.strip().split()[0])
        self.percents = [float(x) for x in header2.strip().split()[1:]]
        self.percent = self.percents[self.component]
        # parse datatable
        read_table_kw['names'] = ["Nucleotide", "Sequence", "Norm_profile",
                                  "Modified_rate", "Untreated_rate"]
        col_offset = 3 * self.component
        bg_col = 3 * self.components + 2
        read_table_kw["usecols"] = [0, 1, 2+col_offset, 3+col_offset, bg_col]
        df = pd.read_table(self.filepath, header=2, **read_table_kw)
        # some rows have an "i" added to the final column
        stripped = []
        for x in df["Untreated_rate"]:
            if type(x) is float:
                stripped.append(x)
            else:
                stripped.append(float(x.rstrip(' i')))
        df["Untreated_rate"] = stripped
        df = df.eval("Reactivity_profile = Modified_rate - Untreated_rate")
        return df


class RNPMaP(Profile):
    def __init__(self, input_data, read_table_kw=None, sequence=None,
                 metric="NormedP", metric_defaults=None):
        if metric_defaults is None:
            metric_defaults = {}
        if read_table_kw is None:
            read_table_kw = {}
        metric_defaults = {
            'NormedP': {
                'metric_column': 'NormedP',
                'color_column': 'RNPsite',
                'cmap': ["silver", "limegreen"],
                'normalization': "none",
                'values': None}
            } | metric_defaults
        read_table_kw = {
            'sep': ','
            } | read_table_kw
        super().__init__(input_data=input_data,
                         read_table_kw=read_table_kw,
                         sequence=sequence,
                         metric=metric,
                         metric_defaults=metric_defaults)


class DeltaProfile(Profile):
    def __init__(self, profile1, profile2, metric=None, metric_defaults=None):
        if metric is None:
            metric = profile1.metric

        columns = ["Nucleotide", "Sequence", metric]
        alignment = data.SequenceAlignment(profile2, profile1)
        profile2 = profile2.get_aligned_data(alignment)
        new_data = pd.merge(
            profile1.data[columns],
            profile2.data[columns],
            how="left", on=["Nucleotide"], suffixes=["_1", "_2"])
        new_data.eval(f"Delta_profile = {metric}_1 - {metric}_2", inplace=True)
        metric_defaults = {
            'Delta_profile': {
                'metric_column': 'Delta_profile',
                'error_column': None,
                'color_column': None,
                'cmap': 'coolwarm',
                'normalization': "min_max",
                'values': [-0.8, 0.8]}
            } | metric_defaults
        super().__init__(
            input_data=new_data,
            sequence=profile1.sequence,
            metric="Delta_profile",
            metric_defaults=metric_defaults)
