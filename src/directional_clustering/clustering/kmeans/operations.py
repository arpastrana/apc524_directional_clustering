from math import fabs

from numpy import array
from numpy import arange
from numpy import random
from numpy import isnan
from numpy import square
from numpy import nonzero
from numpy import mean
from numpy import zeros
from numpy import reshape
from numpy import argmin
from numpy import argmax
from numpy import dot
from numpy import min
from numpy import sum
from numpy import hstack
from numpy import vstack
from numpy import diagonal

from numpy.linalg import norm

from sklearn.metrics.pairwise import pairwise_distances

from time import time


__all__ = ["initialize_kmeans",
           "associate_centroids_cosine",
           "estimate_centroids"]


def rows_squared_norm(M, keepdims=False):
    """
    Calculate the squared norm of the rows of a 2d matrix.
    """
    return square(rows_norm(M, keepdims))


def rows_norm(M, keepdims=False):
    """
    Calculate the norm of the rows of a 2d matrix.
    """
    return norm(M, ord=2, axis=1, keepdims=keepdims)


def initialize_kmeans(X, k, replace=False):
    """
    Initialize k-means routine.

    Input
    -----
    X : `np.array`, shape (n, d)
        2D value matrix where rows are examples.
    k : `int`
        Number of clusters to generate.
    replace : `bool`
        Flag to sample with or without replacement.
        Defaults to `False`.
    
    Returns
    -------
    W : `np.array`, shape (k, d)
        Matrix with cluster centroids, sampled from `X w/o replacement.
    """
    n, d = X.shape
    bag = arange(0, n)
    indices = random.choice(bag, k, replace=replace)
    return X[indices]


def associate_centroids_cosine(X, W):
    """
    Input
    -----
    X : `np.array`, shape (n, d)
        2D value matrix where rows are examples.
    W : `np.array`, shape (k, d)
        2D value matrix where rows are k centroids.
    
    Returns
    -------
    loss : `np.array`
        The mean squared distance to all nearest centroids
    closest_k : `np.array`, shape(n,)
        The closest k-centroid for every example in X.
    """

    xn = rows_norm(X, keepdims=True)
    wn = rows_norm(W, keepdims=True)

    if isnan(wn).any():
        raise Exception("There's a NaN in wn: {}".format(wn))

    X = X / xn

    W = W / wn
    W[nonzero(isnan(W))] = 0.0

    cos_similarity = dot(X, W.T)
    distance = 1 - cos_similarity
    distance = square(distance)

    closest_k = argmin(distance, axis=1)
    loss = mean(min(distance, axis=1))

    return loss, closest_k


def estimate_centroids(X, k, assoc):
    """
    Recalculates centroids.

    Inputs
    ------
    X : `np.array`, shape (n, d)
        Input data, where rows are examples and columns are features.
    k : `int`
        Number of k clusters to generate.
    assoc : `np.array`, shape (n, )
        Index of closest centroid for every example in X.

    Returns
    -------
    W  : `np.array`, shape (k, d)
        The new centroids recalculated based on previous associations.
    """
    n, d = X.shape
    W = zeros((k, d))

    for i in range(k):        
        associated = X[nonzero(assoc==i)]

        if 0 in associated.shape:  # to catch no example associated to i
            centroid = zeros((1, d))
        else:
            centroid = mean(associated, axis=0)  # mean over columns

        W[i] = centroid

    return W


if __name__ == "__main__":

    import numpy as np
    import math


    np.random.seed(4)

    for _ in range(10):
        a = np.random.rand(2, 2)
        b = rows_squared_norm(a)
        c = math.sqrt(a[0,0] ** 2 + a[0,1] ** 2) ** 2
        assert np.allclose(b[0], np.array([c])), "{} != {}".format(b[0], c)

        a = np.random.randn(4, 2)
        b = init_kmeans(a, k=2)
        assert all([b_ in a for b_ in b])

    X = np.linspace(1, 10, 10, dtype=np.float32).reshape(-1, 1)
    X = np.hstack([X, X])

    k = 3
    W = init_kmeans(X, k)
    assert W.shape[0] == k

    W = init_kmeans_farthest(X, k, dist="euclidean", replace=False, epochs=20, eps=1e-3)

    for _ in range(10):
        sq_dist, closest_k = associate_centroids_cosine(X, W)    
        W = estimate_centroids(X, k, closest_k)
    
    assoc, W, losses = kmeans_fit(X, k, epochs=20, eps=1e-3, early_stopping=False)

    for loss in losses:
         print(loss)
    
    print("Tests passed!")