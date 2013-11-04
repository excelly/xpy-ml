from ex import *
from scipy.sparse.linalg import svds

from munkres import GetMunkresIndeces

try:
    from propack import dlansvd, slansvd
    propack = True
except ImportError:
    log.warn('PROPACK cannot be imported')
    propack = False

def ChooseSVD(n, k):
    k = float(k)
    if   n <= 100: return k / n <= 0.02
    elif n <= 200: return k / n <= 0.06
    elif n <= 300: return k / n <= 0.26
    elif n <= 400: return k / n <= 0.28
    elif n <= 500: return k / n <= 0.34
    else:          return k / n <= 0.38

def svdex(A, k = None, method = 'auto'):
    '''partial svd

    (U, s, Vh) = svdex(A, k, method)
    A ~ mul(U*s, Vh)
    '''
    
    m, n = A.shape
    if k is None: k = min(m, n)

    if method == 'svd':
        log.debug('Using svd for {0} matrix'.format((m,n)))

        U, S, Vh = svd(A, False)
        U = U[:, :k]
        Vh = Vh[:k]
        S = S[:k]
    elif method == 'svds':
        log.debug('Using svds svds for {0} matrix'.format((m,n)))
        
        U, S, Vh = svds(A, k)
    elif method == 'lansvd':
        log.debug('Using propack for {0} matrix'.format(A.shape))

        def aprod(transA, m, n, x, y, dparm, iparm, xl, yl):
            if transA.lower()[0] == 't':
                y[:n] = np.dot(A.T, x[:m])
                return 1.0
            else:
                y[:m] = np.dot(A, x[:n])
                return 0.0

        if A.dtype == float64:
            [U, S, V] = dlansvd(aprod, m, n, k, verbose = False)
        elif A.dtype == float32:
            [U, S, V] = slansvd(aprod, m, n, k, verbose = False)
        else: 
            raise ValueError('A must be a float point matrix')
        Vh = V.T
    elif method == 'auto':
        if issparse(A) or ChooseSVD(min(m,n), k):
            if propack:
                return svdex(A, k, 'lansvd')
            else:
                return svdex(A, k, 'svds')
        else:
            return svdex(A, k, 'svd')
    else:
        raise ValueError('unknown svd method: %s' % method)
        
    return (U, S, Vh)
