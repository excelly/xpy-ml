# use kml
# check cluster size

from common import *
from ex.pp import *
from ex.ml.clustering import *

from scipy.special import psi, polygamma, gammaln

def GaussianPDF(X, mus, sigmas, lnpdf = None):

    if lnpdf is None:
        lnpdf = empty((len(X), len(mus)))

    for k in range(len(mus)):
        lnpdf[:,k] = mvnpdf(X, mus[k], sigmas[k])

    return lnpdf

def InitGMM(X, K, method, soft = 0.3):
    n, dim = X.shape
    if method == 'kmeans':
        #centers, dists = vq.kmeans(X, K, 3)
        centers = KML(X, K, verbose = False)[0]
    else:
        centers = X[RI(K, len(X))]
    cl = vq.vq(X, centers)[0]
    mu = zeros((K, dim))
    sigma = zeros((K, dim, dim))
    for k in range(K):
        #mu[k], sigma[k] = MeanCov(X[cl == k])
        mu[k], sigma[k] = MeanCov(X, (float64(cl == k) + soft)/(1 + soft))

    return (mu, sigma)

######################## MGMM
def MGMMGroupLikelihood(group_id, lnpdf, params):

    pi, chi, mu, sigma, gama, phi = params

    l_point = (mul(phi, ln(chi.T+logsafe))*gama[group_id]).sum(1) + (phi*lnpdf).sum(1) - (phi*ln(phi+logsafe)).sum(1) 
    l_group = mul(gama, ln(pi.T+logsafe)) - (gama*ln(gama+logsafe)).sum(1)
    l_all = accumarray(group_id, l_point, l_group)

    return l_all

def MGMMGroupLikelihoodTruth(group_id, lnpdf, params):

    pi, chi, mu, sigma, gama, phi = params
    T = pi.size
    M = gama.shape[0]
    n = lnpdf.shape[0]

    gchiN = zeros((T, M))
    npdf = exp(lnpdf)
    for t in range(T):
        tmp = (npdf*chi[t]).sum(1)
        accumarray(group_id, ln(tmp + logsafe), gchiN[t])

    # avoid numerical issues
    tmp = gchiN.mean(0)
    l = mul(exp(gchiN.T - col(tmp)), col(pi))

    l = ln(l + logsafe).ravel() + tmp
    return l

def MGMMBIC(R, L, rou = 1):
    pi, chi, mu, sigma, gama, phi = R
    D = pi.size-1 + chi.size-chi.shape[0] + mu.size + sigma.size
    bic = L - 0.5*log2(gama.shape[0])*D*rou
    return bic

def FitMGMM_1(X, group_id = None, T = None, K = None, options = None):

    if istuple(X) and group_id == None:
        X, group_id, T, K, options = X

    SeedRand()

    init, epsilon, maxIter, verbose = GetOptions(
        options, 'init', 'kmeans', 
        'epsilon', 1e-4, 'maxIter', 50, 'verbose', True)

    n, dim = X.shape
    M = arguniqueInt(int32(group_id)).size
    lnpdf = zeros((n, K))

    pi = random.rand(T); pi = pi/pi.sum()
    chi = random.rand(T, K); chi = chi/col(chi.sum(1))

    tic('MGMM')
    mu, sigma = InitGMM(X, K, init)

    gama = random.rand(M, T); gama = gama/col(gama.sum(1))
    phi = random.rand(n, K); phi = phi/col(phi.sum(1))
    
    l = zeros(maxIter)
    lnpdf = GaussianPDF(X, mu, sigma, lnpdf)
    for iter in range(maxIter):
        # update phi
        gama_logchi = exp(mul(gama, ln(chi + logsafe)))
        phi = gama_logchi[group_id]*exp(lnpdf + col(500 - lnpdf.max(1)))#numerical
        phi = phi*col(1/phi.sum(1))
        
        # update gama
        logchi_phiT = mul(ln(chi + logsafe), phi.T)
        for t in range(T):
            gama[:,t] = accumarray(group_id, logchi_phiT[t], zeros(M))
        gama = gama - col(gama.max(1) + 500)
        gama = exp(gama) * pi
        gama = gama*col(1/gama.sum(1))

        # update pi
        pi = gama.mean(0)

        # update chi
        chi = mul(gama[group_id].T, phi)
        chi = chi*col(1/chi.sum(1))

        # update Gaussians
        for k in range(K):
            mu[k], sigma[k] = MeanCov(X, phi[:,k])

        # reset bad ones
        # vs = arr([trace(ss) for ss in sigma])
        # vthresh = vs.max()*1e-2
        # for k in range(K):
        #     if vs[k] < vthresh:
        #         log.warn('Reset collapsing component')
        #         mu[k], sigma[k] = MeanCov(X[RI(len(X)/K, len(X))])
        #         if iter > 0: l[iter - 1] = -inf

        lnpdf = GaussianPDF(X, mu, sigma, lnpdf)
        
        l[iter] = MGMMGroupLikelihood(group_id, lnpdf, (pi, chi, mu, sigma, gama, phi)).sum()

        if verbose:
            log.info('--Iter = %d, L = %g, Time elapsed = %0.2f', 
                     iter, l[iter]/M, toc('MGMM', show = False))

        if iter > 0 and (l[iter] - l[iter - 1])/M < epsilon:
            break

    if verbose:
        l_true = MGMMGroupLikelihoodTruth(group_id, lnpdf, (pi, chi, mu,sigma, gama, phi)).sum()
        log.info('MGMM converged. Var L = %g, True L = %g' % (l[iter], l_true))

    return ((pi, chi, mu, sigma, gama, phi), l[iter])

################# GLDA
def glda_alpha_obj(alpha, pg, sym = True):
    '''the objective of glda-alpha
    '''

    M, K = pg.shape
    if sym:
        f = M*(gammaln(K*alpha) - K*gammaln(alpha)) + (alpha - 1)*pg.sum()
    else:
        f = M*(gammaln(alpha.sum()) - gammaln(alpha).sum()) + mul(pg, (alpha - 1)).sum()

    return -f

def glda_alpha_grad(alpha, pg, sym = True):
    '''the gradient of glda-alpha
    '''

    M, K = pg.shape
    if sym:
        g = M*K*(psi(K*alpha) - psi(alpha)) + pg.sum()
    else:
        g = M*(psi(alpha.sum()) - psi(alpha)) + pg.sum(0)

    return -g

def glda_alpha_hess(alpha, pg, sym = True):
    ''' the hession of glda-alpha
    '''

    M, K = pg.shape
    if sym:
        return -M*(polygamma(1, K*alpha)*K*K - polygamma(1, alpha)*K)
    else:
        return -M*(polygamma(1, alpha.sum()) - diag(polygamma(1, alpha)))

def GLDAGroupLikelihood(group_id, lnpdf, pg, params):

    alpha, mu, sigma, gama, phi = params
    l_point = (phi*pg[group_id]).sum(1) + (phi*lnpdf).sum(1) - (phi*ln(phi + logsafe)).sum(1) 
    l_group = gammaln(alpha.sum()) - gammaln(alpha).sum() + mul(alpha - 1, pg.T) - gammaln(gama.sum(1)) + gammaln(gama).sum(1) - diag(mul(gama - 1, pg.T)) 
    l_all = accumarray(group_id, l_point, l_group)

    return l_all

def GLDABIC(R, L, rou = 1):
    alpha, mu, sigma, gama, phi = R
    D = alpha.size + mu.size + sigma.size
    bic = L - 0.5*log2(gama.shape[0])*D*rou
    return bic

def FitGLDA_1(X, group_id = None, K = None, options = None):

    if istuple(X) and group_id is None:
        X, group_id, K, options = X
    SeedRand()

    init, symmetric, epsilon, maxIter, verbose = GetOptions(
        options, 'init', 'kmeans', 'symmetric', False,  
        'epsilon', 1e-4, 'maxIter', 50, 'verbose', True)

    n, dim = X.shape
    M = arguniqueInt(int32(group_id)).size
    lnpdf = zeros((n, K))

    tic('GLDA')
    mu, sigma = InitGMM(X, K, init)

    alpha = random.rand(K) + 1; alpha = alpha * (K/alpha.sum())
    gama = repmat(alpha, (M,1))
            
    l = zeros(maxIter)
    pg = psi(gama) - col(psi(gama.sum(1)))
    lnpdf = GaussianPDF(X, mu, sigma, lnpdf)
    for iter in range(maxIter):
        # update phi
        epg = exp(pg)
        phi = epg[group_id]*exp(lnpdf + col(500 - lnpdf.max(1)))
        phi = np.array(phi*col(1/phi.sum(1)), copy = True, order = 'F')

        # update Gaussians
        for k in range(K):
            mu[k], sigma[k] = MeanCov(X, phi[:,k])

        # reset bad ones
        # vs = arr([trace(ss) for ss in sigma])
        # vthresh = vs.max()*1e-2
        # for k in range(K):
        #     if vs[k] < vthresh:
        #         log.warn('Reset collapsing component')
        #         mu[k], sigma[k] = MeanCov(X[RI(len(X)/K, len(X))])
        #         if iter > 0: l[iter - 1] = -inf

        lnpdf = GaussianPDF(X, mu, sigma, lnpdf)

        # update gama
        for k in range(K):
            gama[:,k] = accumarray(group_id, phi[:,k], zeros(M))
        gama = gama + alpha
        pg = psi(gama) - col(psi(gama.sum(1)))

        # update alpha
        if symmetric: alpha = arr([alpha[0]])
        alpha, obj, stat = fmin_l_bfgs_b(
            glda_alpha_obj, alpha, glda_alpha_grad, args = (pg, symmetric), 
            bounds = [(1e-10, None)]*len(alpha), m = 20, factr = epsilon/eps, 
            pgtol = epsilon, maxfun = 20, iprint = -1)
        check(stat['warnflag'] < 2, 'Optimization error: ' + stat['task'])
        if symmetric: alpha = alpha*ones(K)

        l[iter] = GLDAGroupLikelihood(group_id, lnpdf, pg, (alpha, mu, sigma, gama, phi)).sum()

        if verbose:
            log.info('--Iter = %d, L = %g, Time elapsed = %0.2f', 
                     iter, l[iter]/M, toc('GLDA', show = False))

        if iter > 0 and (l[iter] - l[iter-1])/M < epsilon:
            break

    return ((alpha, mu, sigma, gama, phi), l[iter])

def FitMGMM(X, group_id = None, T = None, K = None, options = None):
    if istuple(X) and group_id is None:
        X, group_id, T, K, options = X
    SeedRand()

    ntry, nproc, verbose = GetOptions(
        options, 'ntry', 10, 'nproc', 1, 'verbose', True)

    log.info('MGMM for {0} data. M={1}, T={2}, K={3}'.format(
            X.shape, arguniqueInt(int32(group_id)).size, T, K))

    jobs = [(X, group_id, T, K, options)]*ntry
    R, L = unzip(ProcJobs(FitMGMM_1, jobs, nproc))

    ii = argmax(L)
    L = L[ii]
    R = R[ii]

    return (R, L) # (pi, chi, mu, sigma, gama, phi)

def FitGLDA(X, group_id = None, K = None, options = None):

    if istuple(X) and group_id is None:
        X, group_id, K, options = X
    SeedRand()

    ntry, nproc, verbose = GetOptions(
        options, 'ntry', 10, 'nproc', 1, 'verbose', True)

    log.info('GLDA for {0} data. M={1}, K={2}'.format(
            X.shape, arguniqueInt(int32(group_id)).size, K))

    jobs = [(X, group_id, K, options)]*ntry
    R, L = unzip(ProcJobs(FitGLDA_1, jobs, nproc))

    ii = argmax(L)
    L = L[ii]
    R = R[ii]

    return (R, L) # (alpha, mu, sigma, gama, phi)

def FitMGMM_BICSearch(X, group_id, Ts, Ks, options):

    rou, nproc_bic = GetOptions(options, 'bic_coeff', 1, 'nproc_bic', 1)
    
    n, dim = X.shape
    log.info('BIC search for {0} data with {1} processces'.format(X.shape, nproc_bic))

    tt, kk = MeshGrid(Ts, Ks)
    TKs = hstack((col(tt), col(kk)))
    jobs = [(X, group_id, tk[0], tk[1], options) for tk in TKs]
    RL = ProcJobs(FitMGMM, jobs, nproc_bic)
    BICs = [MGMMBIC(rl[0], rl[1], rou) for rl in RL]
    R, L = unzip(RL)

    stat = hstack((TKs, col(arr(L)), col(arr(BICs)))) # (T,K,L,BIC)

    ii = argmax(BICs)
    R = R[ii]
    L = L[ii]

    log.info('T = {0}, K = {1} selected'.format(
            TKs[ii, 0], TKs[ii, 1]))

    return (R, L, stat)

def FitGLDA_BICSearch(X, group_id, Ks, options):

    rou, nproc_bic = GetOptions(options, 'bic_coeff', 1, 'nproc_bic', 1)
    
    n, dim = X.shape
    log.info('BIC search for {0} data with {1} processces'.format(X.shape, nproc_bic))

    jobs = [(X, group_id, k, options) for k in Ks]
    RL = ProcJobs(FitGLDA, jobs, nproc_bic)
    BICs = [GLDABIC(rl[0], rl[1], rou) for rl in RL]
    R, L = unzip(RL)

    stat = hstack((col(arr(Ks)), col(arr(L)), col(arr(BICs)))) # (T,K,L,BIC)

    ii = argmax(BICs)
    R = R[ii]
    L = L[ii]

    log.info('K = {0} selected'.format(Ks[ii]))

    return (R, L, stat)

if __name__=='__main__':
    InitLog()

    from ex.plott import *
    from gmm import GMM

    T = 2
    K = 3
    M = 100
    mean_N = 100

    N_bad_instance = 1
    N_bad_group = 1

#    pi_gt = random.rand(T) + 1; 
    pi_gt = ones(2);
    pi_gt = pi_gt/pi_gt.sum()
    chi_gt = arr([[1, 1, 0],[1, 0, 1]]) + 1e-2
    chi_gt = Normalize(chi_gt, 's1', 'row')[0]
    mu_gt = arr([[-1, -1], [1, -1], [0, 1]])
    sigma_gt = 3e-2

    # simulate data
    y_gt = randm(pi_gt, M)
    theta_gt = chi_gt[y_gt]
    N = random.poisson(mean_N, M)
#    N = random.exponential(mean_N, M)
    cN = cat(([0], cumsum(N)))
    z_gt = zeros(cN[-1])
    X = zeros((cN[-1], mu_gt.shape[1]))
    group_id = zeros(cN[-1], int32)
    g_type = zeros(M)
    gmm = GMM(theta_gt[0], mu_gt, sigma_gt);
    for m in range(M):
        gmm.priors = theta_gt[m]
        X[cN[m]:cN[m+1]], z_gt[cN[m]:cN[m+1]] = gmm.GenerateSample(N[m])
        group_id[cN[m]:cN[m+1]] = m

    # anomalies
    for ind in range(N_bad_instance):
        m =RI(1, M)
        g_type[m] = 1
        X[group_id == m] = random.randn((group_id == m).sum(), 
                                    mu_gt.shape[1])*0.5
    for ind in range(N_bad_group):
        m =RI(1, M)
        g_type[m] = 2

        gmm.priors = [0, 1, 1]
        idx = group_id == m;
        X[idx], z_gt[idx]= gmm.GenerateSample(sum(idx));

    ncol = 5;
    base = 5*vstack(((arange(M) % ncol), floor(arange(M)/ncol))).T

    options = {'ntry':5, 'nproc':1, 'nproc_bic':10, 'init':'kmeans', 'bic_coeff':10.0, 
               'epsilon':1e-5, 'maxIter':50, 'verbose':True, 'symmetric':True}

    fig = figure()

    # # MGMM
    R, L = FitMGMM(X, group_id, T, K, options)
    mu = R[2]; sigma = R[3]
    lnpdf = GaussianPDF(X, mu, sigma)
    l_var = MGMMGroupLikelihood(group_id, lnpdf, R)
    l_true = MGMMGroupLikelihoodTruth(group_id, lnpdf, R)

    log.info('True likelihood = %g, Var likelihood = %g' % (l_true.sum(), l_var.sum()))
    
    subplot(fig, 121)
    scatter(X[:,0] + base[group_id,0], X[:,1] + base[group_id,1], c = l_true[group_id], edgecolors='none')
    title('MGMM');    draw()
    log.info("MGMM Corr between N and likelihood: %g" % np.corrcoef(N.ravel(), l_var.ravel())[0,1])

    # GLDA
    R, L = FitGLDA(X, group_id, K, options)
    alpha = R[0]; mu = R[1]; sigma = R[2]; gama = R[-2]
    lnpdf = GaussianPDF(X, mu, sigma)
    pg = psi(gama) - col(psi(gama.sum(1)))
    l_var = GLDAGroupLikelihood(group_id, lnpdf, pg, R)
    
    subplot(fig, 122)
    scatter(X[:,0] + base[group_id,0], X[:,1] + base[group_id,1], c = l_var[group_id], edgecolors = 'none')
    title('GLDA');    draw()
    log.info('Alpha = {0}'.format(alpha))
    log.info("GLDA Corr between N and likelihood: %g" % np.corrcoef(N.ravel(), l_var.ravel())[0,1])

#    sys.exit(0)
    ###### BIC functions

    options['verbose'] = False
    Ts = arange(3, 7)[::-1]
    Ks = arange(3, 7)[::-1]

    fig2 = figure()
    # MGMM
    R, L, stat = FitMGMM_BICSearch(X, group_id, Ts, Ks, options)
    print stat

    mu = R[2]; sigma = R[3]
    lnpdf = GaussianPDF(X, mu, sigma)
    l_mgmm = MGMMGroupLikelihood(group_id, lnpdf, R)
    
    subplot(fig2, 121)
    scatter(X[:,0] + base[group_id,0], X[:,1] + base[group_id,1], c = l_mgmm[group_id], edgecolors='none')
    title('MGMM');    draw()
    log.info("MGMM Corr between N and likelihood: %g" % np.corrcoef(N.ravel(), l_var.ravel())[0,1])

    # GLDA
    R, L, stat = FitGLDA_BICSearch(X, group_id, Ks, options)
    print stat

    alpha = R[0]; mu = R[1]; sigma = R[2]; gama = R[-2]
    lnpdf = GaussianPDF(X, mu, sigma)
    pg = psi(gama) - col(psi(gama.sum(1)))
    l_glda = GLDAGroupLikelihood(group_id, lnpdf, pg, R)
    
    subplot(fig2, 122)
    scatter(X[:,0] + base[group_id,0], X[:,1] + base[group_id,1], c = l_glda[group_id], edgecolors = 'none')
    title('GLDA');    draw()
    log.info("GLDA Corr between N and likelihood: %g" % np.corrcoef(N.ravel(), l_var.ravel())[0,1])
    log.info('Alpha = {0}'.format(alpha))

    show()
