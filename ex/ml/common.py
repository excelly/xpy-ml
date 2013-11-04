from ex import *
from ex.nnsearch import *
from ex.alg import svdex
from scipy.optimize import fmin_l_bfgs_b
from scipy.cluster import vq

def GetConfusionMatrix(label, y, align=False):
    '''get the confusion matrix according to the true label and the
    predicted class y. useful in clustering and multiclass.  

    if align, then the rows of the confusion matrix will be permuted
    so that its trace is maximized. useful in clustering.'''

    label=arr(label).ravel().astype(int32)
    y=arr(y).ravel().astype(int32)

    # encode the labels
    ul = np.unique(label)
    label = EncodeArray(label, ul)
    y = EncodeArray(y, ul)

    # construct the confusion matrix
    n = ul.size
    cm = accumarray(vstack((label, y)), 1, (n, n))

    # maximize the trace
    if align:
        from ex.alg.munkres import GetMunkresIndeces
        pidx=GetMunkresIndeces((-cm).tolist())
        cm=cm[pidx]

    return (cm, ul)

def ResultStat(label, y, verbose=True):
    '''get the classification statistics
    '''
    
    label=arr(label).ravel() > 0.5
    y=arr(y).ravel() > 0.5
    n=label.size

    true_pos=sum(AND(label, y))*1.0
    correct=sum(label == y)*1.0

    accuracy=correct/n
    precision=true_pos/y.sum()
    recall=true_pos/label.sum()
    fscore=2*recall*precision/(recall + precision)

    if verbose:
        log.info('Acc: %0.2f%% (%g/%g). Rec: %0.2f%% (%g/%g). Pre: %0.2f%% (%g/%g). F-score: %0.2f%%'%(accuracy*100, correct, n, 100*recall, true_pos, label.sum(), 100*precision, true_pos, y.sum(), 100*fscore))

    return (accuracy, precision, recall, fscore)

def GetROC(y, score):
    '''(precision recall ap)=GetROC(y, score)
    calculate the ROC curve and average precision
    y: labels
    score: scores
    return (average precision, precisions, recalls)
    '''

    y=float64(y).ravel()
    score=float64(score).ravel()

    n=len(y)
    check(len(score) == n, "length should match")

    ii=score.argsort()[::-1]
    score=score[ii]
    y=float64(y[ii] > 0.5)
    tp=y.sum()

    chits=y.cumsum() # accumulative hits
    precision=chits/arange(1,n + 1)
    recall=chits/tp

    hits=hstack((chits[0], diff(chits)))
    check((hits >= 0).all() and hits.sum() == tp)
    ap=emul(precision, hits).sum()/tp

    return((ap, precision, recall))

def NNClassify(te_data, tr_data, tr_label=None, use_kdtree=False, nproc=1):
    '''classification by the nearest neighbor
    '''

    if use_kdtree:
        edges = KDTNNSearch(tr_data, (te_data, 1), 'knn', nproc)
    else:
        edges = BrutalNNSearch(tr_data, (te_data, 1), 'knn', nproc)
    
    idx = int64(edges[1])
    if tr_label is None: 
        return idx
    else:
        return tr_label[idx]

try:
    import kml
except:
    log.warn('Cannot use KML')

def KML(X, K, method = 3, maxIter = 50, verbose = False):
    '''kmeans-local (birch) fast clustering.
    X: n x dim data matrix.
    K: number of clusters.
    method: method of algorithm. 0-Lloyds, 1-Swap, 2-EZ_Hybrid, 3-Hybrid (recommended).
    '''

    n, dim=X.shape
    if verbose:
        log.info("KML input: N={0}, Dim={1}, Clusters={2}".format(n, dim, K));

    centers = zeros((K, dim), dtype=float32)
    distortion = kml.KML(float32(X), centers, method, maxIter, int(verbose))

    return (centers, distortion)

def Quantize(X, codebook, kdtree = False, nproc = 1):
    '''quantize vectors

    if codebook is really a codebook, then codebook is used to
    quantize X, and the code is returned 

    if codebook is a scalar, then it is the size of the codebook. and (codebook, code) is returned
    '''

    codebook = arr(codebook)
    if codebook.size == 1:
        K = codebook
        codebook = KML(X, K)[0]
        code = NNClassify(X, codebook, use_kdtree = kdtree, nproc = nproc)
        return (codebook, code)
    else:
        code = NNClassify(X, codebook, use_kdtree = kdtree, nproc = nproc)
        return code


def UV_LS(X, rk, nu=1e-5, U=None, V=None, nIter=1):
    '''use alternating least squares to get X=U'*V
    '''

    m, n=X.shape
    if U is None: U=random.rand(rk, m)*0.1
    if V is None: V=random.rand(rk, n)*0.1

    ridge=eye(rk)*nu;
    for ind in range(nIter):
        U=solve(mul(V, V.T) + ridge, mul(X, V.T).T)
        V=solve(mul(U, U.T) + ridge, mul(U, X))
    
    return (U, V, 0.5*nu*(sos(U) + sos(V)))

def UV_NMF(X, rk, U=None, V=None, nIter=1):
    '''nmf factorization
    '''

    m, n=X.shape
    if U is None: U=random.rand(rk, m)*0.1 + 1e-3;
    if V is None: V=random.rand(rk, n)*0.1 + 1e-3;

    epsilon=1e-10
    for ind in range(nIter):
        E=mul(V, V.T)
        dE=diag(E)
        E=SetDiag(E, 0)
        T=mul(V, X.T)
        for ii in range(rk):
            U[ii]=maximum(epsilon, (T[ii] - mul(E[ii], U))/dE[ii])

        E=mul(U, U.T)
        dE=diag(E)
        E=SetDiag(E, 0)
        T=mul(U, X)
        for ii in range(rk):
            V[ii]=maximum(epsilon, (T[ii] - mul(E[ii], V))/dE[ii])

    return (U, V)

def UV_SVD(X, rk):
    '''use svd to get X=U'V
    '''

    U, S, Vh = svdex(X, rk)
    return (U.T*col(sqrt(S)), Vh*col(sqrt(S)))
	
def EffRank(ev, thresh=0.99):
    '''get the effective rank given the eigenvalues.
        
    s: the vector of eigen values. if you have sigular values, square
    them before passing in.  
    thresh: energy to preserve.
    '''

    ev = arr(ev)
    if ev.min() < -1e-5:
        raise ValueError("not a proper eigenvalue array: {0}".format(ev))
    ev[ev < 0] = 0

    ev = sort(ev)[::-1]
    ce = ev.cumsum()

    return min(len(ev), (ce/ce[-1] <= thresh).sum() + 1)

import ex.pp.mr as mr

class CVObject(mr.BaseMapper):
    '''k-fold cross-validation facility.
    '''

    def __init__(self, n, k = 10):
        '''construct a CVParition object.

        n: number of samples.
        k: number of folds.
        '''

        mr.BaseMapper.__init__(self, 'CV')

        self.N = n
        self.K = k

        self.RePartition()

    def RePartition(self):
        '''redo the random partition
        '''

        chunk_size = ceil(self.N*1./self.K)
        rp = random.permutation(self.N)
        self.TestSets = Partition(rp.tolist(), chunk_size)

        check(len(self.TestSets) == self.K, 
                  'test sets wrong')

    def TestInd(self, ind):
        '''return the i-th test set indeces
        '''

        return self.TestSets[ind]

    def TrainInd(self, ind):
        '''return the i-th training set
        '''

        idx = set(range(self.N)).difference(self.TestSets[ind])
        return list(idx)

    def NumFolds(self):
        return len(self.TestSets)

    def TestSizes(self):
        return [len(s) for s in self.TestSets]

    def TrainSizes(self):
        return [self.N - len(s) for s in self.TestSets]
        
    def __str__(self):
        return '''K-fold cross-validation partition: 
N: {0}, 
K: {1}, 
Sizes of Training sets: {2},
Sizes of Test sets: {3}'''.format(self.N, self.NumFolds(), self.TrainSizes(), self.TestSizes())

    def Map(self, key, val):
        '''process each fold using mapreduce
        '''

        trI, teI = val
        result = self.func(trI, teI, self.X, self.y, self.options)

        return (key, result)

    def CV(self, func, X, y, options, poolsize = 1):
        '''cross-validation with parallelization

        func is a function result = func(trI, teI, X, y, *params)
        X should be a design matrix

        A list of K tuples (training sample index, test sample index, result of func) will be returned.
        '''

        # store the data
        self.func = func
        self.X = X
        self.y = y
        self.options = options

        # making the jobs
        jobs = []
        II = []
        for ind in range(self.NumFolds()):
            trI = self.TrainInd(ind)
            teI = self.TestInd(ind)
        
            jobs.append((ind, (trI, teI)))
            II.append((trI, teI))

        # do the jobs
        engine = mr.MapEngine(self, poolsize)
        results = engine.Start(jobs)

        trI, teI = unzip(II)
        keys, results = unzip(results)
        return (trI, teI, results)

##### tests
if __name__ == '__main__':
    InitLog()

    ap,a,b=GetROC([1,1,0,0,1],[1,2,3,4,5])
    test(eq(ap,0.7), "GetROC")

    gridsize=10
    X, Y=MeshGrid(range(gridsize), range(gridsize))
    points=hstack((vec(X), vec(Y))).astype(float64)

    centers=arr([[0, 0.],[9, 0.]])
    labels=NNClassify(points, centers, use_kdtree=True)
    test((labels == 0).sum() == 50, 'NNClassify')
    labels=NNClassify(points, centers, use_kdtree=False)
    test((labels == 0).sum() == 50, 'NNClassify')

    test(EffRank([1,0,0,1]) == 2,"effrank")

    X=col(arr([1,2, 8,9, 20,21]))
    centers, dist=KML(X, 3, maxIter=10, verbose=0)
    test(dist == 0.25, 'KML')

    codebook, code = Quantize(X, 3)
    test(code.sum() == 6, 'quantize')

    m=100
    n=100
    A=random.rand(m,n)

    U, V, dummy = UV_LS(A, 5, nIter=3)
    test(sos(A - mul(U.T, V)) < 800, 'UV_LS')

    U, V = UV_NMF(A, 5, nIter=3)
    test(sos(A - mul(U.T, V)) < 800, 'UV_NMF')

    U, V = UV_SVD(A, 5)
    test(sos(A - mul(U.T, V)) < 800, 'UV_SVD')
