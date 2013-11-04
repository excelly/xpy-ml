from common import *

def mlr_obj(beta, X, YK, lam, weights):
    '''the objective of multi-logistic
    '''

    n, dim = X.shape
    K = YK.shape[1]
    beta = beta.reshape((dim, K - 1))

    Xbeta = mul(X, beta)
    Z = exp(Xbeta).sum(1) + 1

    if weights is None:
        return loge(Z).sum() - spmask(Xbeta, YK[:, :-1]).sum() + 0.5*lam*ss(beta[:-1])
    else:
        return dot(weights, loge(Z)) - dot(weights, spmask(Xbeta, YK[:, :-1]).sum(1)) + 0.5*lam*ss(beta[:-1])

def mlr_grad(beta, X, YK, lam, weights):
    '''the gradient of multi-logistic
    '''

    n, dim = X.shape
    K = YK.shape[1]
    beta = beta.reshape((dim, K - 1))

    P = exp(mul(X, beta))
    P = P*col(1/(P.sum(1) + 1))

    if weights is None:
        grad = mul(X.T, arr(P - YK[:, :-1]))
    else:
        grad = mul(X.T*weights, arr(P - YK[:, :-1]))

    penalty_beta = lam*beta
    penalty_beta[-1] = 0

    return arr(grad + penalty_beta).ravel()

class MultiLogistic:
    '''multinomial logistic regression
    '''

    def __init__(self):
        self.options, self.beta, self.normalizer = (None,)*3

    def Train(self, X, y, options = None):
        self.options = options
        lam, normalize, weights, init, maxIter, epsilon, verbose = GetOptions(
            self.options, 'lam', 1e-3, 'normalize', True, 'weights', None, 'init', None, 
            'maxIter', 100, 'epsilon', 1e-5, 'verbose', True)

        self.n, self.dim = X.shape
        if normalize:
            X, self.normalizer = Normalize(X, '+-1', 'col')
        else:
            self.normalizer = (None,)*2
        X = hstack((X, ones((self.n, 1))))

        y = int32(y)
        self.ulabels = unique(y)
        K = len(self.ulabels); check(K > 1, 'needs at least 2 classes')
        y = EncodeArray(y, self.ulabels)
        YK = ssp.csr_matrix((ones(self.n),vstack((arange(self.n),y.ravel()))), (self.n, K))

        # start point
        if init is None or init.beta is None:
            self.beta = ones((self.dim + 1, K - 1))*1e-3
        else:
            self.beta = init.beta

        if verbose: log.info('Training {0}multi-logistic. Data={1} x {2}. #class = {3}'.format(
                'weighted ' if weights is not None else '', self.n, self.dim, K))
        
        if weights is not None:
            weights = weights.ravel()

        self.beta, fopt, stat = fmin_l_bfgs_b(mlr_obj, self.beta.ravel(), mlr_grad, args=(X, YK, lam, weights), m = 100, 
                                              factr=epsilon/eps, pgtol=epsilon, maxfun=maxIter, iprint=verbose if verbose else -1)

        self.beta = self.beta.reshape((self.dim + 1, K - 1))
        self.opt_stat = stat

    def Predict(self, X):
        '''prediction using multi-logistic model
        '''

        X = Normalize(X, self.normalizer, 'col')[0]
        n = X.shape[0]
        X = hstack((X, ones((n, 1), X.dtype)))
        P = hstack((expex(mul(X, self.beta)), ones((n, 1))))
        P = Normalize(P, 's1', 'row')[0]

        t = argmax(P, 1)
        p = P[(arange(n), t)]
        t = self.ulabels[t]

        return (t, p, P)

    def Plot(self, xlim, ylim, color = 'label', gridsize = 50):
        '''plot the current classifier
        '''

        check(self.dim == 2, 'can only plot in 2-D space')
        X, Y = MeshGrid(linspace(xlim[0], xlim[1], gridsize),
                        linspace(ylim[0], ylim[1], gridsize))
        F = hstack((col(X), col(Y)))

        y, p = self.Predict(F)[:2]

        if color == 'label':
            scatter(X.ravel(), Y.ravel(), c = y, edgecolors = 'none')
        elif color == 'prob':
            scatter(X.ravel(), Y.ravel(), c = p, vmin = 0, vmax = 1, edgecolors = 'none')
        draw()

    def CV(self, nfolds, X, y, options, verbose = True, poolsize = 1):
        '''doing cross-validation for multi-logistic model.
        
        nfolds is the number of fold.
        returns (predicted class, probability of the prediction)
        '''

        cvo = CVObject(y.size, nfolds)
        if verbose:
            log.info('Cross-validating MultiLogistic. Data = {0}'.format(X.shape))
            log.info(cvo)

        trI, teI, perf = cvo.CV(ipred, X, y, options, poolsize)
        t, p = unzip(perf)

        idx = arr(Flatten(teI))
        t = arr(Flatten(t), int32)
        p = arr(Flatten(p))

        t[idx]=t.copy()
        p[idx]=p.copy()

        return (t, p)

    def Clone(self):
        return deepcopy(self)

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
            Copy(o, self)
        else:
            data=LoadMat(filename)
            Copy(data, self)

def ipred(trI, teI, X, y, options):
    '''used for cross validation
    '''

    model = MultiLogistic()
    if options.get('weights', None) is not None:
        options = deepcopy(options)
        options['weights'] = options['weights'][trI]
    model.Train(X[trI], y[trI], options)
    
    if model.opt_stat['warnflag'] > 1:
        raise RuntimeError('bad optimization')

    t, p, P = model.Predict(X[teI])

    return (t.tolist(), p.tolist())

if __name__ == '__main__':

    InitLog()

    n = 1000
    pts = arr([range(n), range(n/2) + range(n/2, 0, -1)]).T
    y = cat((ones(n/2)*3, ones(n/2)*7))
    
    weights = random.rand(n)*0.1 + 1
    model = MultiLogistic()
    t, p = model.CV(10, pts, y, {'weights':weights, 'verbose':False})
    acc = (y == t).mean()
    test(acc > 0.95, "MultiLogistic Train & Test & CV")

    model.Train(pts, y, {'lam':1})
    subplot(gcf(), 211)
    model.Plot(GetRange(pts[:,0]), GetRange(pts[:,1]), 'label')
    subplot(gcf(), 212)
    model.Plot(GetRange(pts[:,0]), GetRange(pts[:,1]), 'prob')
    show()
