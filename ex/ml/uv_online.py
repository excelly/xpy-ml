from factorization import *

class UVOL:
    '''online factorization
    '''

    def __init__(self, dim, k):
        self.dim = int(dim)
        self.k = int(k)

    def Factorize(self, x_src, T, batch_size = 1, epsilon = 1e-3, maxIter = 2, verbose = True):
        '''online factorization using data from src the generator
        '''

        D = eye(self.dim, self.k)
        A = zeros((self.k, self.k))
        B = zeros((self.dim, self.k))
        check(batch_size >= 1, 'bad batch size')

        ridge = eye(self.k)*1e-5
        t = 0
        while t < T:
            # retrieve data
            x_t = hstack([col(x_src.next()) for i in range(min(batch_size, T - t))])
            t += x_t.shape[1]

            alpha_t = solve(mul(D.T, D) + ridge, mul(D.T, x_t))
            
            tmp = alpha_t.T*(1.0/batch_size)
            A += mul(alpha_t, tmp)
            B += mul(x_t, tmp)

            D = solve(A + ridge, B.T).T
            # for s in range(maxIter):
            #     old = D.copy()

            #     for jnd in range(self.k):
            #         u_j = (B[:,jnd] - mul(D, A[:,jnd]))*(1/A[jnd,jnd]) + D[:,jnd]
            #         nu = norm(u_j)
            #         D[:,jnd] = u_j if nu <= 1 else u_j*(1/nu)

            #     if norm(old - D)/norm(D) < epsilon:
            #         break

            if verbose:
                if (t/batch_size) % 100 == 0: log.info('Processed %d batches' % t)

        return D.T

    def Factorize_X(self, X, passes = 1, batch_size = 1, epsilon = 1e-3, maxIter = 2, verbose = True):
        '''online factorization
        '''

        def src(X):
            ind = 0
            guard = len(X) - 1
            while True:
                yield X[ind]
                ind = ind + 1 if ind < guard else 0

        m, n = X.shape
        if verbose: log.info('Factorizing {0} matrix online using {1} passes'.format(X.shape, passes))

        V = self.Factorize(src(X), passes*m, batch_size, epsilon, maxIter, verbose)
        U = solve(mul(V, V.T), mul(V, X.T))

        return (U, V)

if __name__ == '__main__':
    InitLog()

    m=500
    n=200
    rk=50
    A=mul(random.randn(m,rk), random.randn(rk, n)) + random.randn(m,n)*0.1*sqrt(m)
    k=10

    f = UVOL(n, k)
    tic()
    U, V = f.Factorize_X(A, 1, int(round(m/100.0)))
    t_ol = toc(show = False)
    err_ol = rmse(A - mul(U.T, V))

    tic()
    U_svd, S_svd, V_svd = svdex(A, k)
    t_svd = toc(show = False)
    err_svd=rmse(mul(U_svd*S_svd, V_svd.T) - A)

    log.info('The RMSE ratio for UVOL/SVD is %g, the Time ratio is %g (%g, %g)' % (err_ol/err_svd, t_ol/t_svd, t_ol, t_svd))
