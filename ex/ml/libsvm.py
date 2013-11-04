from common import *

import ex.ml.libsvm.svmutil as su

def a2l(X, y = None):
    '''convert arrays to list
    '''
    
    if y is not None:
        y = y.tolist()
	    
    if issparse(X):
        X = [dict(zip(find(row)[1], row.data)) for row in X]
    else:
        X = X.tolist()

    if y is not None:
        return (X, y)
    else:
        return X

class LibSVM:
    '''libsvm
    '''

    def __init(self):
        self.n, self.dim, self.options, self.model, self.ulabels, self.preproc_param = [None]*6

    def Train(self, X, y, options = None):
        ''' train libsvm model
        '''

        # process labels
        y = int32(y)
        self.ulabels = unique(y)
        K = len(self.ulabels)
        check(K > 1, 'needs at least 2 classes')
        y = EncodeArray(y, self.ulabels)

        # process features
	self.n, self.dim = X.shape
        X, self.preproc_param = Normalize(X, '+-1', 'col')

        # train
	X, y = a2l(X, y)
        if options is None: # default parameter
            options = '-s 0 -t 2 -c 1 -m 1000'
	self.model = su.svm_train(y, X, options + ' -b 1 -q')

    def Predict(self, X):
        ''' predict for test data
        '''

        # apply preprocessing
        X = Normalize(X, self.preproc_param, 'col')[0]

        X = a2l(X)
	t, acc, P = su.svm_predict(zeros(len(X), dtype = int32), X, self.model, '-b 1')
        t = arr(t, dtype = 'int32')
        P = arr(P)

        # extract results
        t = self.ulabels[t]
	p=P.max(1)

	return (t, p, P)

    def CV(self, nfolds, X, y, options = None, verbose = True, poolsize = 1):
        ''' get cross-validation performance
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
        SavePickle(filename, self)

    def Load(self, filename):
        o=LoadPickles(filename)
        Copy(o, self)

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

def ipred(trI, teI, X, y, options):
    '''used for cross validation
    '''

    model = LibSVM()
    model.Train(X[trI], y[trI], options)
    t, p, P = model.Predict(X[teI])

    return (t.tolist(), p.tolist())

if __name__ == '__main__':
    InitLog()

    n = 100
    pts = vstack((repmat(linspace(-1, 1, n/2), (1, 2)),
                  hstack((sin(linspace(0, 10, n/2)) + 0.8, sin(linspace(0, 10, n/2)) - 0.8)))).T * 10
    y = cat((ones(n/2)*3, ones(n/2)*7))
    
    model = LibSVM()
    t, p = model.CV(10, pts, y)
    acc = (t == y).mean()
    print '** Acc: %f' % acc
    test(acc > 0.95, "LibSVM Train & Test & CV")

    model.Train(pts, y, '-s 0 -t 2 -c 10000')
    t, p, P = model.Predict(pts)
    acc = (y == t).mean()
    print '** Acc: %f' % acc

    subplot(gcf(), 131);
    plot(pts[:,0], pts[:,1], '+')
    subplot(gcf(), 132)
    model.Plot(GetRange(pts[:,0]), GetRange(pts[:,1]), 'label', 100)
    subplot(gcf(), 133)
    model.Plot(GetRange(pts[:,0]), GetRange(pts[:,1]), 'prob', 100)
    show()
