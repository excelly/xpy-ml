from ex import *
from ex.alg.common import svdex
import rpca

#@profile
def DRMF(X, K, e = 0.05, options = None):
    '''[ L, S ] = DRMF(M, K, e, options)
    direct robust matrix factorization
    M: input matrix
    K: max rank
    e: percentage of outliers
    L: Low rank result
    S: sparse outliers
    '''

    init, max_iter, epsilon, verbose = GetOptions(
        options, 'init', None, 'max_iter', 50, 
        'epsilon', 1e-3, 'verbose', True);

    m, n = X.shape

    if init is None:
        L = rpca.RPCA(A, maxIter=7)[0]
    else:
        L = init;

    if verbose:
        log.info('DRMF for %dx%d matrix. K=%d, e=%0.1f%%' % (
                m, n, K, e*100))

    tic('drmf')
    objs = zeros(max_iter)
    for it in range(max_iter):
        C, S = ProjectClean(X, L, e)
        L = ProjectLowRank(C, K)
    
        objs[it] = rmse(C - L)
        if verbose:
            log.info('Iter=%d, Rank=%d, |E|_0=%d, Obj=%g, Time=%0.3f' % (
                    it, K, sum(fabs(S.ravel()) > 1e-10), objs[it], toc('drmf','',False)));

        if it > 0 and ((objs[it-1]-objs[it])/objs[it-1] < epsilon or objs[it] < 1e-7): 
            break

    return (L, S)

def ProjectClean(X, L, e):
    m, n = X.shape
    S = X - L

    aS = fabs(S)
    thresh  = quantile(aS, 1-e)
    S[aS <= thresh] = 0

    return (X - S, S)

def ProjectLowRank(X, K):
    U, s, Vh = svdex(X, K);
    return mul(U*s, Vh)

if __name__ == '__main__':
    InitLog()

    rk = 10
    m = 500
    ratio_ol = 0.01
    num_ol = int(round(m*m*ratio_ol))

    BG = mul(randn(rk, m).T, randn(rk, m))/rk
    OL = zeros((m, m))
    for ind in range(num_ol):
        ij = random.randint(0, m, 2)
        OL[ij[0], ij[1]] = 5 + rand(1)*10

    A = BG + OL
    A_hat, S_hat = DRMF(A, rk, ratio_ol)

    A_svd = svdex(A, rk)
    A_svd = mul(A_svd[0]*A_svd[1], A_svd[2])

    log.info('DRMF RMSE = %f, SVD RMSE = %f' % (
            rmse(BG-A_hat), rmse(BG-A_svd)))
    test(rmse(BG-A_hat) < 1e-5, 'DRMF recovering L')
