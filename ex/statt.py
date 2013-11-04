from common import *

def randm(p, n):
    '''multinomial random sampling
    '''

    p = arr(p)
    if p.size == 1:
        cp = linspace(1.0/p, 1, p)
    else:
        cp = cumsum(p)
        if fabs(cp[-1] - 1) > 1e-10:
            raise ValueError('wrong multinomial')

    d = row(cp) - col(random.rand(n))
    return argmin((d <= 0)*2 + d, 1).astype(int32)

def mvnpdf(X, mu = 0, sigma = None, logpdf = False):
    '''multivariate normal pdf
    '''

    if X.ndim == 1: X = row(X)
    n, dim = X.shape
    X = X - mu

    if sigma is None: sigma = eye(dim)
    try:
        R = chol(sigma).T
    except:
        ridge = svdex(sigma, 1)[1]*1e-5
        log.debug('singular covariance. adjusting with %g' % ridge)
        R = chol(sigma + eye(dim)*ridge).T

    xRinv = solve(R.T, X.T).T
    logSqrtDetSigma = ln(diag(R)).sum()

    quadform = (xRinv**2).sum(1)
    f = -0.5*quadform - logSqrtDetSigma - 0.5*dim*ln(2*pi)
    if logpdf:
        return f
    else:
        return exp(f)

if __name__ == "__main__":
    InitLog()

    p = arr([1.,2,3,4]); p = p/p.sum()
    sample = randm(p, 1e6)
    a = accumarray(sample, 1, zeros(4))
    test(fabs(p - a/a.sum()) < 1e-2, 'randm')

    mu = zeros((1,2))
    sigma = eye(2)
    p = mvnpdf(arr([0., 0]), mu, sigma)
    test(eq(p, 0.15915, 1e-4), 'mvnpdf')
