from ex import *
from common import *

class NBayes:
    '''naive bayes classifier
    '''

    def __init__(self):
        self.n, self.dim, self.options, self.pC, self.meanFC, self.stdFC = [None]*6

    def Train(self, X, y, options = None):
        self.options = options
        prior = GetOptions(
            self.options, 'prior', 'empirical')

        self.n, self.dim = X.shape
        y = int32(y)
        self.ulabels = unique(y)
        K = len(self.ulabels)
        check(K > 1, 'needs at least 2 classes')
        y = EncodeArray(y, self.ulabels)

        # find class members
        members = [L2I(y == i) for i in range(K)]

        # train class priors
        if prior == 'empirical':
            self.pC = arr([len(members[i]) for i in range(K)])
        else:
            self.pC = ones(K)
        self.pC = self.pC/self.pC.sum()

        # train feature conditionals
        self.meanFC = empty((K, self.dim))
        self.stdFC = empty((K, self.dim))
        for c in range(K):
            x = X[members[c]]
            if x.size == self.dim: # if only one sample
                raise ValueError("two samples at least")

            self.meanFC[c] = x.mean(0)
            self.stdFC[c] = x.std(0, ddof = 1)

    def Predict(self, X):
        '''prediction using multi-logistic model
        '''
        
        if X.ndim == 1: X = row(X)

        n, dim = X.shape
        check(dim == self.dim, 'dim not right')

        K = len(self.ulabels)

        P = empty((n, K), dtype = float64)
        for c in range(K):
            mu = self.meanFC[c]
            sigma = self.stdFC[c]

            logp = -0.5*((X - mu)*(1.0/sigma))**2 - loge(sigma)# vectorized
            P[:,c] = loge(self.pC[c]) + logp.sum(1)

        t = argmax(P, 1)
        P = exp(P - col(P.max(1))) # avoid underflow
        P = P*col(1.0/P.sum(1))

        return (self.ulabels[t], P[(arange(n), t)], P)

    def __str__(self):
        return "Naive Bayes model. #Class = {0}, Dim = {1}".format(
            len(self.ulabels), self.dim)

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

    def CV(self, nfolds, X, y, options = None, verbose = True, poolsize = 1):
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

    model = NBayes()
    model.Train(X[trI], y[trI], options)
    t, p, P = model.Predict(X[teI])
    return (t.tolist(), p.tolist())

if __name__ == '__main__':

    InitLog()

    n = 1000
    pts = arr([range(n), range(n/2) + range(n/2, 0, -1)]).T
    y = cat((ones(n/2)*3, ones(n/2)*7))
    
    model = NBayes()
    t, p = model.CV(10, pts, y)
    acc = (y == t).mean()
    test(acc == 1, "NaiveBayes Train & Test & CV")

    model.Train(pts, y)
    subplot(gcf(), 211)
    model.Plot(GetRange(pts[:,0]), GetRange(pts[:,1]), 'label')
    subplot(gcf(), 212)
    model.Plot(GetRange(pts[:,0]), GetRange(pts[:,1]), 'prob')
    show()
