from common import *
from ex.plott import *
from ex.pp import *

class GMM:
    '''gaussian mixure model
    '''
    def __init__(self, weights = None, means = None, covars = None):
        '''initialize the parameters.

        means: size [K, dim] each row is a mean vector
        covars: size [K, dim, dim]
        '''

        if weights is not None:
            self.weights = arr(weights)
            self.means = arr(means)

            covars = arr(covars)
            if covars.ndim == 0:
                self.covars = repmat(eye(self.dim())*covars, (len(self.weights), 1, 1))
            elif covars.ndim == 2:
                self.covars = repmat(covars, (len(self.weights), 1, 1))
            else:
                self.covars = covars

            check(len(self.weights) == len(self.means) and len(self.weights) == len(self.covars), 'parameter wrong')

    def dim(self):
        return self.means.shape[1]

    def GenData(self, n):
        '''generate samples from the current moddel
        '''

        ncomp = len(self.weights)
        dim = self.dim()
        weights = float64(self.weights)/self.weights.sum()

        labels = randm(weights, n); 
        data = zeros((n, dim))
        for c in range(ncomp):
            idx = (labels == c)
            data[idx] = random.multivariate_normal(self.means[c], self.covars[c], (idx.sum(),))

        return (data, labels)

    def Fit(self, X, K, options = None):
        '''fit a gaussian mixture model
        '''

        init, epsilon, maxIter, verbose = GetOptions(
            options, 'init', 'kmeans',
            'epsilon', 1e-5, 'maxIter', 50, 'verbose', True)

        n, dim = X.shape
        K = int(K)
		
        centers = X[RI(K, len(X))]
        cl = vq.vq(X, centers)[0]
        mu = zeros((K, dim))
        sigma = zeros((K, dim, dim))
        for k in range(K):
            mu[k], sigma[k] = MeanCov(X[cl == k])

        pi = ones(K)/K;
        # EM
        tic('gmm')
        l = zeros(maxIter)
        lnpdf = zeros((K, n))
        for k in range(K):
            lnpdf[k] = mvnpdf(X, mu[k], sigma[k], True)
        for iter in range(maxIter):
            # E
            gama = col(pi)*exp(lnpdf + (500 - lnpdf.max(0)))
            gama = Normalize(gama, 's1', 'col')[0]

            # M
            pi = gama.sum(1)
            pi = pi/pi.sum()

            for k in range(K):
                mu[k], sigma[k] = MeanCov(X, gama[k])

            # vs = arr([trace(ss) for ss in sigma])
            # vthresh = vs.max()*1e-2
            # for k in range(K):
            #     if vs[k] < vthresh:
            #         log.warn('Reset collapsing component')
            #         mu[k], sigma[k] = MeanCov(X[RI(len(X)/K, len(X))])
            #         if iter > 0: l[iter - 1] = -inf

            # update the Gaussian pdf
            for k in range(K):
                lnpdf[k] = mvnpdf(X, mu[k], sigma[k], True)

            # compute likelihood
            l[iter] = GMMLikelihood(lnpdf, (pi, mu, sigma)).sum()

            if verbose:
                log.info('--Iter = %d, L = %g, Time elapsed = %0.2f' % (iter, l[iter], toc('gmm', show = False)))

            if iter > 0 and (l[iter] - l[iter - 1])/n < epsilon:
                break

        self.means = mu
        self.covars = sigma
        self.weights = pi
        self.n = n
        self.L = l[iter]

        return ((pi, mu, sigma), l[iter])

    def Save(self, filename):
        '''save the model to file
        '''

        format=filename.split('.')[-1].lower()
        check(format in ['pkl','mat'], 'unknown file format')

        if format == 'pkl':
            SavePickle(filename, self)
        else:
            SaveMat(filename, self.__dict__)

    def Load(self, filename):
        '''load a model from file
        '''

        format=filename.split('.')[-1].lower()
        check(format in ['pkl','mat'], 'unknown file format')

        if format == 'pkl':
            o=LoadPickles(filename)
            CopyAttributes(o, self)
        else:
            data=LoadMat(filename)
            CopyAttributes(data, self)

    def Plot(self, n = 1000):
        data, labels = self.GenData(n)
        scatter(data[:,0], data[:,1], c = labels, edgecolors = 'none')
        draw()

def FitGMM_1(X, K = None, options = None):
    if istuple(X) and K is None:
        X, K, options = X
    SeedRand()
    gmm = GMM()
    return gmm.Fit(X, K, options)

def FitGMM(X, K = None, options = None):
    if istuple(X) and K is None:
        X, K, options = X

    ntry, nproc, verbose = GetOptions(
        options, 'ntry', 10, 'nproc', 1, 'verbose', True)

    log.info('GMM for {0} data. K = {1}'.format(
            X.shape, K))

    jobs = [(X, K, options)]*ntry
    R, L = unzip(ProcJobs(FitGMM_1, jobs, nproc))

    ii = argmax(L)
    L = L[ii]
    R = R[ii]

    return (R, L) # (pi, mu, sigma)

def GMMLikelihood(lnpdf, params):
    pi, mu, sigma = params
    return ln(mul(row(pi), exp(lnpdf)) + logsafe)

def GMMBIC(params, L, n, rou = 1):
    pi, mu, sigma = params
    D = pi.size - 1 + mu.size + sigma.size
    bic = L - 0.5*log2(n)*D*rou
    return bic

def FitGMM_BICSearch(X, Ks, options = None):
    rou, nproc_bic = GetOptions(options, 'bic_coeff', 1, 'nproc_bic', 1)

    n, dim = X.shape
    log.info('BIC search for {0} data with {1} processes'.format(X.shape, nproc_bic))
    
    jobs = [(X, k, options) for k in Ks]
    RL = ProcJobs(FitGMM, jobs, nproc_bic)
    BICs = [GMMBIC(rl[0], rl[1], n, rou) for rl in RL]
    R, L = unzip(RL)

    stat = hstack((col(arr(Ks)), col(arr(L)), col(arr(BICs)))) # (K, L, BIC)
        
    ii = argmax(BICs)
    R = R[ii]
    L = L[ii]

    log.info('K = {0} selected'.format(Ks[ii]))

    gmm = GMM(R[0], R[1], R[2])
    return (gmm, L, stat)

if __name__ == '__main__':
    InitLog()
    fig = figure(1)
    
    subplot(fig, 121)
    gmm = GMM([1, 1, 1], [[0, 1], [1, 0], [0, 0]], 0.01)
    gmm.Plot(10000)
    print 'Original model'
    print gmm.means
    print gmm.covars
    
    subplot(fig, 122)
    X, labels = gmm.GenData(1000)
    gmm.Fit(X, 3, {'epsilon':-10000000})
    gmm.Plot(10000)
    print 'Fitted model'
    print gmm.means
    print gmm.covars

    model, L, stat = FitGMM_BICSearch(X, arange(2, 6), 
                     {'nproc_bic':1, 'verbose':False})
    print stat
    test(argmax(stat[:,2]) == 1, 'GMM BIC search')

    show()
