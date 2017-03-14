""" PCA + clustering analysis
http://stackoverflow.com/questions/27491197/scikit-learn-finding-the-features-that-contribute-to-each-kmeans-cluster
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter,ScalarFormatter, FormatStrFormatter
import numpy as np
import math
import pandas as pd
from sklearn.decomposition import PCA
import scipy as sp
from numpy import linalg as LA
import statsmodels.api as sm

__VAREXPLAIN = 0.90 # 90% variance calculation

def dim_red_pca(x_orig, d=0, corr=False):
    r"""
    Performs principal component analysis.

    Parameters
    ----------
    x_orig : array, (n, d)
        Original observations (n observations, d features)

    d : int
        Number of principal components (default is ``0`` => all components).

    corr : bool
        If true, the PCA is performed based on the correlation matrix.

    Notes
    -----
    Always all eigenvalues and eigenvectors are returned,
    independently of the desired number of components ``d``.

    Returns
    -------
    Xred : array, (n, m or d)
        Reduced data matrix

    e_values : array, (m)
        The eigenvalues, sorted in descending manner.

    e_vectors : array, (n, m)
        The eigenvectors, sorted corresponding to eigenvalues.

    """

    # Normalise data
    x_normalised = (x_orig - x_orig.mean(0)) / x_orig.std(0)

    # Compute correlation / covariance matrix
    if corr:
        CO = np.corrcoef(x_orig.T)
    else:
        CO = np.cov(x_orig.T)

    #  WITH USING PCA from numpy
    e_values, e_vectors = LA.eig(CO)

    # Sort the eigenvalues and the eigenvectors descending
    idx = np.argsort(e_values)[::-1]
    e_vectors = -1*e_vectors[:, idx]
    e_values = e_values[idx]

    # Get the number of desired dimensions
    d_e_vecs = e_vectors

    if d == 0:
        # run a algo to check how many factors explain 90% of variance
        cum_vars = 0.
        for d in range(0, len(e_values)):
           cum_vars += e_values[d]
           if cum_vars/ sum(e_values) > __VAREXPLAIN:
               break

    d_e_vecs = e_vectors[:, :d]

    # Project original data onto the PC factors
    PC_Ret = np.dot(x_orig, d_e_vecs)
    return PC_Ret, e_values, d_e_vecs,d