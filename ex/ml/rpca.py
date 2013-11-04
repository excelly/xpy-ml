from ex import *
from ex.alg.common import svdex

def RPCA(D, lam = None, tol = 1e-7, maxIter = 500):
    '''Yi Ma's robust pca
    
    return (L, SingularValues(L))
    '''

    m, n = D.shape
    maxmn, minmn = (max(m, n), min(m, n))
    lam = float(lam) if lam is not None else 1.0
    log.info('RPCA for %dx%d matrix. lambda = %f.' % (m, n, lam))

    lam = lam/sqrt(maxmn)
    Y = D.copy()
    norm_two = svdex(Y, 1); norm_two = norm_two[1][0]
    norm_inf = norm(Y.ravel(), inf) / lam
    dual_norm = max(norm_two, norm_inf)
    Y = Y / dual_norm

    A_hat = zeros((m, n))
    E_hat = zeros((m, n))
    mu = 1.25/norm_two
    mu_bar = mu*1e7
    rho = 1.5
    d_norm = norm(D, 'fro')

    sv = 10
    for it in range(maxIter):
        temp_T = D - A_hat + (1/mu)*Y;
        E_hat[:] = 0;
        filt = temp_T > lam/mu;
        E_hat[filt] = temp_T[filt] - lam/mu
        filt = temp_T < -lam/mu;
        E_hat[filt] = temp_T[filt] + lam/mu

        U, diagS, Vh = svdex(D - E_hat + (1/mu)*Y, sv)

        svp = sum(diagS > 1/mu);
        if svp < sv:
            sv = min(svp + 1, minmn)
        else:
            sv = min(svp + round(0.05*minmn), minmn)
        A_hat = mul(U[:,:svp]*(diagS[:svp] - 1/mu), Vh[:svp])

        Z = D - A_hat - E_hat

        Y = Y + mu*Z
        mu = min(mu*rho, mu_bar)

        # stop criterion
        stop = norm(Z, 'fro') / d_norm
        converged = stop < tol
        log.info('Iter=%d, rank=%d, |E|_0=%d, Stop=%g' % (
                it, svp, sum(fabs(E_hat.ravel()) > 1e-10), stop))

        if converged: break

    return (A_hat, diagS[:svp])

if __name__ == '__main__':
    InitLog()

    rk = 10
    m = 500
    num_ol = int(round(m*m*0.01))

    BG = mul(randn(rk, m).T, randn(rk, m))/rk
    OL = zeros((m, m))
    for ind in range(num_ol):
        ij = random.randint(0, m, 2)
        OL[ij[0], ij[1]] = 5 + rand(1)*10

    A = BG + OL
    A_hat = RPCA(A)[0]

    A_svd = svdex(A, rk)
    A_svd = mul(A_svd[0]*A_svd[1], A_svd[2])

    log.info('RPCA RMSE = %f, SVD RMSE = %f' % (
            rmse(BG-A_hat), rmse(BG-A_svd)))
    test(rmse(BG-A_hat) < 1e-5, 'RPCA recovering L')
