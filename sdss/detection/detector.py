from ex import *
from ex.ml import *
import ex.nnsearch as nn
import ex.annsearch as ann

def PCAScore_Model(X, pca, method = 'accum_err'):
    '''get the anomaly scores using global pca method
    '''

    method = method.lower()
    check(method in ['rec_err', 'accum_err', 'dist', 'dist_out', 'accum_dist_out'], 'unknown method: ' + method)

    n, dim = X.shape
    R = pca.R
    L = pca.L

    log.info('PCA Detecting using {0}'.format(method))
    log.info('Data: {0} x {1}. R = {2}'.format(n, dim, R))

    if method == 'rec_err':# reconstruction error
        P = pca.Project(X, arange(R, dim))
        scores = sqrt(sos(P, 1))
    elif method == 'accum_err':# accumulative reconstruction error
        P = pca.Project(X, arange(R, dim))
        P = scale(P, arange(P.shape[1]) + 1, 0)
        scores = sqrt(sos(P, 1))
    elif method == 'dist':# manalanobis distance from the mean
        end = min(dim, (L2I(L > L[R]*1e-3)).argmax() + 1)
        P = pca.Project(X, arange(end))
        P = scale(P, 1/sqrt(L[:end]), 0)
        scores = sqrt(sos(P, 1))
    elif method == 'dist_out':
        end = min(dim, (L2I(L > L[R]*1e-3)).argmax() + 1)
        P = pca.Project(X, arange(R, end))
        P = scale(P, 1/sqrt(L[R:end]), 0)
        scores = sqrt(sos(P, 1))
    elif method == 'accum_dist_out':
        end = min(dim, (L2I(L > L[R]*1e-3)).argmax() + 1)
        P = pca.Project(X, arange(R, end))
        P = scale(P, 1/sqrt(L[R:end]), 0)
        P = scale(P, arange(P.shape[1]) + 1, 0)
        scores = sqrt(sos(P, 1))

    return scores


def PCAScore(X_tr, X_te, E, method = 'accum_err'):
    '''get the anomaly scores using global pca method
    '''

    method = method.lower()
    check(method in ['rec_err', 'accum_err', 'dist', 'dist_out', 'accum_dist_out'], 'unknown method: ' + method)

    n, dim = X_te.shape

    pca = PCA.Train(X_tr, E)
    pca.R = min(50, max(2, pca.R))

    return PCAScore_Model(X_te, pca, method)

def KNNScore(X_tr, X_te, K, method = 'max_dist', nproc = 1):
    '''get the anomaly scores using KNN method
    '''

    method = method.lower()
    check(method in ['mean_dist', 'max_dist'],
          'unknown method: ' + method)
    n, dim = X_te.shape

    log.info('Searching for {0}NN, Dim = {1}'.format(K, dim))
    edges = nn.BrutalNNSearch(X_tr, (X_te, K+1), 'knn', nproc)

    scores = KNNScoreEdges(edges, method)
    return (scores, edges)

def KNNScoreEdges(edges, method = 'max_dist'):
    n = edges[0].max() + 1
    K = (edges[0] == 0).sum() - 1
    if method=='mean_dist':
        scores = accumarray(int32(edges[0]), edges[2], zeros(n), 0)/K
    elif method=='max_dist':
        scores = accumarray(int32(edges[0]), edges[2], zeros(n), 2)
    else:
        raise ValueError('unknown scoring method')
    return scores
