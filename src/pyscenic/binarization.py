# coding=utf-8

import pandas as pd
from sklearn import mixture
import numpy as np
import matplotlib.pyplot as plt


__alls__ = ['binarize']


def _derive_threshold(auc_mtx: pd.DataFrame, regulon_name: str) -> float:
    assert auc_mtx is not None and not auc_mtx.empty
    assert regulon_name in auc_mtx.columns
    # Fit a two component Gaussian Mixture model on the AUC distribution using an Expectation-Maximization algorithm.
    data = auc_mtx[regulon_name].values.reshape(-1, 1)
    gmm = mixture.GaussianMixture(n_components=2, covariance_type='full').fit(data)
    avgs = gmm.means_
    stds = np.sqrt(gmm.covariances_.reshape(-1, 1))

    # The threshold is based on the distribution with the highest mean and is defined as (mu - 2 x std)
    idx = np.argmax(avgs)
    threshold = max(avgs[idx] - 2 * stds[idx], 0)
    # This threshold cannot be lower than (mu + 2 x std) based on the distribution with the lowest mean.
    idx = np.argmin(avgs)
    lower_bound = avgs[idx] + 2 * stds[idx]

    return max(lower_bound, threshold)

def binarize(auc_mtx: pd.DataFrame) -> (pd.DataFrame, pd.Series):
    """
    "Binarize" the supplied AUC matrix, i.e. decide if for each cells in the matrix a regulon is active or not based
    on the bimodal distribution of the AUC values for that regulon.

    :param auc_mtx: The dataframe with the AUC values for all cells and regulons (n_cells x n_regulons).
    :return: A "binarized" dataframe and a series containing the AUC threshold used for each regulon.
    """
    def derive_thresholds(auc_mtx):
        return pd.Series(index=auc_mtx.columns, data=[_derive_threshold(auc_mtx, name) for name in auc_mtx.columns])
    thresholds = derive_thresholds(auc_mtx)
    return (auc_mtx > thresholds).astype(int), thresholds

def plot_binarization(auc_mtx: pd.DataFrame, regulon_name: str, bins: int=200) -> None:
    """
    Plot the "binarization" process for the given regulon.

    :param auc_mtx: The dataframe with the AUC values for all cells and regulons (n_cells x n_regulons).
    :param regulon_name: The name of the regulon.
    :param bins: The number of bins to use in the AUC histogram.
    """
    auc_mtx[regulon_name].hist(bins=bins)
    threshold = _derive_threshold(auc_mtx, regulon_name)
    ylim = plt.ylim()
    plt.plot([threshold]*2, ylim, 'r:')
    plt.ylim(ylim)
    plt.xlabel('AUC')
    plt.ylabel('#')
    plt.title(regulon_name)
