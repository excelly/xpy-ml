from factorization import *
from sputil import *
from ex.alg.propack import dlansvd

class UVRP:
    '''factorization using random projection
    '''

    def __init__(self, m, k, d = None, beta = 0.5, eta = 5.0):
        '''set the choice of d
        '''

        self.m = int(m)
        self.k = int(k)
        self.beta = beta*0.2
        self.eta = eta

        self.d = self.GetRPDim(m, k) if (d is None or d <= 0) else d
        self.RPMat = self.GetRPMat(m, self.d)

    def GetRPDim(self, m, k):
        '''get the suggested value of d for UVRP
        '''

        d=2*max(k, sqrt(k)*loge(m*1.0/self.beta))*max(loge(k), -loge(self.beta))/self.eta
        return int(round(max(k, min(m, d))))

    def GetRPMat(self, m, d):
        '''generate a random projection matrix for UV_RP
        '''

        # sample rows
        omega=random.permutation(m)[:d]
        omega.sort()

        # construct DCT matrix
        u=arange(m, dtype=float64)
        F=cos(mul(col(u[omega]), row((u + 0.5)*pi/m)))/sqrt(m*0.5)
        if omega[0] == 0: F[0] = F[0]/sqrt(2)

        # make the random projection
        D = (random.rand(m) > 0.5).astype(int32)*2 - 1
        return F*D*sqrt(m*1.0/d)

    def Factorize(self, fAprod, m, n, tA = False, verbose = True):
        '''factorization using random projection. A = U'*V

        if tA, then factorize trans(A) instead of A
        '''

        if tA: m, n = (n, m)
        check(m == self.m, 'wrong input matrix')
        if verbose:
            log.info('UVRP for {0} x {1} matrix with k = {2}, d = {3}'.format(
                m, n, self.k, self.d))

        tic('UVRP')
        B = qr(fAprod(not tA, m, n, self.RPMat.T), econ = True)[0]
        U = svdex(fAprod(tA, m, n, B), self.k)[0]
        V = fAprod(not tA, m, n, U).T
        t = toc('UVRP', show = False)

        if verbose:
            log.info('UVRP finished in %g seconds.' % (t));
        return (U.T, V)

    def Factorize_X(self, A, tA = False, verbose = True):
        '''factorization using random projection. A = U'*V
        '''

        if tA: A = A.T
        def aprod(trans, m, n, x):
            return mul(A.T if trans else A, x)

        m, n = A.shape
        U, V = self.Factorize(aprod, m, n, False, verbose)
        return (U, V) if not tA else (V, U)

    def MMF(self, fAprod, fOutlier, m, n, lam, tA = False, 
            maxIter = 100, epsilon = 1e-4, verbose = True):
        '''disk-based robust factorization using random projection

        fAprod(trans, m, n): calculate y = Ax.

        fOutlier(U, V, lam): calculate the outliers in A given
        factorization U'V and threshold lam
        '''

        if tA: m, n = (n, m)
        log.info('''RPMMF for {0} x {1} matrix. k = {2}, d = {3}, lambda = {4}'''.format(m, n, self.k, self.d, lam))

        tic('RPMMF')
        RPXt = fAprod(not tA, m, n, self.RPMat.T)
        R = ssp.csr_matrix(([1e-5], ([0],[0])), (m, n))

        for ind in range(maxIter):
            old = R

            # update U and V
            B = qr(RPXt - mul(R.T, self.RPMat.T), econ = True)[0]
            U = svdex(fAprod(tA, m, n, B) - mul(R, B), k)[0]
            V = fAprod(not tA, m, n, U).T - mul(U.T, R)

            # update R
            if not tA:
                R = fOutlier(U, V, lam)
            else:
                R = fOutlier(V, U, lam)

            change = sqrt(ss(R - old)/ss(old))
            if verbose:
                log.info('-Iter=%d, Change=%g, Time=%0.5f'%(ind, change, toc("RPMMF", show=False)));

            if change < epsilon or isnan(change):
                break

        return (U.T, V, R) if not tA else (V, U.T, R)

    def MMF_X(self, A, lam, tA = False, a_type = 'E', l0 = False, maxIter = 100, epsilon = 1e-4, verbose = True):
        '''robust factorization using random projection
        '''

        if tA: A = A.T
        def aprod(trans, m, n, x):
            return mul(A.T if trans else A, x)

        m, n = A.shape
        ssA = ss(A, 0)
        def outlier(U, V, lam):
            if a_type == 'E':
                R = SThresh(A - mul(U, V), lam, l0)
            else:
                ssE=ssA - ss(V, 0)
                if l0: ii=ssE > 2*lam
                else: ii=sqrt(ssE) > lam
                
                if ii.sum() > 0: R=zeros((n, m), A.dtype)
                else: R=ssp.lil_matrix((n, m), dtype = A.dtype)

                if ii.any():
                    if l0: R[ii]=(A[:, ii] - mul(U, V[:, ii])).T
                    else: R[ii]=scale(A[:, ii] - mul(U, V[:, ii]), 1 - lam/col(ssE[ii]), 0).T

                if issparse(R): R=R.tocsc().T
                else: R=R.T

            # objective
            if verbose:
                if a_type == 'E': numnz=find(R)[0].size
                elif a_type == 'R': numnz=(ss(R, 0) > 1e-10).sum()

                obj = [0.5*ss(A - mul(U, V) - R), 0]
                if l0:
                    obj[1]=lam*numnz
                else: 
                    if a_type == 'E': obj[1]=lam*fabs(R).sum()
                    elif a_type == 'R': obj[1]=lam*sqrt(ss(R, 0)).sum()

                log.debug('Obj=%g (%g, %g), NNZ=%d' % (sum(obj), obj[0], obj[1], numnz))

            return R
    
        U, V, R = self.MMF(aprod, outlier, m, n, lam, False, maxIter, epsilon, verbose)
        return (U, V, R) if not tA else (V, U, R)

if __name__ == '__main__':
    InitLog()

    m=5000
    n=2000
    rk=50
    A=mul(random.randn(m,rk), random.randn(rk, n)) + random.randn(m,n)*0.1*sqrt(m)
    k = 10

    f = UVRP(m, k)
    test(eq((f.RPMat**2).max(), 2.0/f.d, 1e-5), 'RP matrix')
    
    tic()
    U_rp, V_rp = f.Factorize_X(A)
    t_rp = toc(show=False)
    err_rp=rmse(mul(U_rp.T, V_rp) - A)

    f = UVRP(n, k)
    test(eq((f.RPMat**2).max(), 2.0/f.d, 1e-5), 'RP matrix')

    tic()
    U_rpt, V_rpt = f.Factorize_X(A, tA = True)
    t_rpt = toc(show=False)
    err_rpt=rmse(mul(U_rpt.T, V_rpt) - A)

    tic()
    U_svd, S_svd, V_svd = svdex(A, k)
    t_svd = toc(show = False)
    err_svd=rmse(mul(U_svd*S_svd, V_svd.T) - A)

    log.info('RMSE ratio for UVRP/SVD=%g/%g, Time ratio is %g/%g (%g, %g, %g)' % (err_rp/err_svd, err_rpt/err_svd, t_rp/t_svd, t_rpt/t_svd, t_rp, t_rpt, t_svd))

############ MMF

    B = A.copy()
    B[1,1] = 100

    f = UVRP(m, k)
    lam = 70
    U, V, R = f.MMF_X(B, lam, a_type = 'E', l0 = False)
    rnz = find(R)
    test(rnz[0].size == 1 and rnz[0][0]==1 and rnz[1][0]==1, 'RPMMF')

    f = UVRP(n, k)
    lam = 70
    U, V, R = f.MMF_X(B, lam, tA = True, a_type = 'E', l0 = False)
    rnz = find(R)
    test(rnz[0].size == 1 and rnz[0][0]==1 and rnz[1][0]==1, 'RPMMF')
