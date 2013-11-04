from common import *
from ex.pp import *
import pyflann as flann

_global_data = None
def _init_global(data):
    global _global_data
    _global_data = data

def BuildTree(X, method = 'kdtree', precision = 1):
    '''build a search tree for X

    method: 'kdtree', 'brutal', or 'auto'
    '''

    tree = flann.FLANN()

    if method == 'kdtree':
        tree.build_index(X, target_precision=precision, algorithm='kdtree')
    elif method == 'brutal':
        tree.build_index(X, target_precision=precision, algorithm='linear')
    elif method == 'auto':
        tree.build_index(X, target_precision=precision, algorithm='autotuned')
    else:
        raise ValueError('unknown nn method')

    return tree

def KNN_1(tree, target = None):
    '''find knn neighbors of target in tree. target is tuple (X, K)

    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''

    if target is None: tree, target = tree
    if tree is None: tree = _global_data

    X, K = target
    idx, dists = tree.nn_index(X, K)

    edges = vstack((kron(arange(len(X)), ones(K)),
                    idx.ravel(), dists.ravel()))
    return edges

def SNN_1(tree, target = None):
    '''find sphere neighbors of target in tree. target is tuple (X, radius)
    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''


    if target is None: tree, target = tree
    if tree is None: tree = _global_data

    X, r = target
    
    idx, dist = zip(*[tree.nn_radius(x, r) for x in X])
    base = [ones(len(idx[ii]))*ii for ii in range(len(idx))]

    edges = vstack((hstack(base),
                    hstack(idx), 
                    hstack(dist)))
    return edges

def NNSearch(tree, target, method='knn', nproc=1, verbose=False):
    '''find neighbors of target in tree.
    if tree is not a FLANN but a data set, then a FLANN is built.

    method can be 'knn' or 'sphere'
    if knn, then target is (X, K)
    if sphere, then target is (X, radius)
    
    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''

    check(method in ['knn', 'sphere'], 'unknown method')
    
    X, param = target

    if verbose:
        log.info('{0} search for {1} {2}-D points using {3} processes'.format(method, len(X), X.shape[1], nproc))

    if not isinstance(tree, flann.FLANN):
        tree = BuildTree(tree)

    func = KNN_1 if method == 'knn' else SNN_1
    if nproc == 1:
        result = func(tree, target)
    else:
        X_chunks = Partition(X, len(X)/nproc/2)
        sizes = arr([len(chunk) for chunk in X_chunks])
        jobs = [(None, (chunk, param)) for chunk in X_chunks]
        results = ProcJobs(func, jobs, nproc, _init_global, tree)

        for ind in range(len(results)):
            results[ind][0] += sizes[:ind].sum()

        result = hstack(results)

    return MakeCont(result)

def Edges2Bags(edges, nNode = None):
    '''convert edges produced by search algorithm to bags of
    neighbors, For example, [[1,1,2,2,2],[1,2,3,4,5]] -> [[1,2],
    [3,4,5]].  

    return a list of bags, one bag for one node. each bag is a matrix [neighbor nodes; distances]
    '''
    if nNode is None: nNode = edges[:2].max() + 1

    groups = GroupArray(edges[0], arange(edges.shape[1]), nNode)
    for ind in range(nNode):
        groups[ind] = edges[1:, groups[ind]]

    return groups

if __name__=='__main__':

    InitLog()

    gridsize=50

    X, Y=MeshGrid(range(gridsize), range(gridsize))

    data=float32(hstack((col(X), col(Y))))

    nproc = 2

    log.info('test started')

    K = 5
    r = 2.5

    tree = BuildTree(data, 'brutal')
    knn_br_s = NNSearch(tree, (data, K), 'knn', 1)
    log.info('sequtial brutal knn finished')
    knn_br_p = NNSearch(tree, (data, K), 'knn', nproc)
    log.info('parallel brutal knn finished')
    snn_br_s = NNSearch(tree, (data, r), 'sphere', 1)
    log.info('sequtial brutal sphere finished')
    snn_br_p = NNSearch(tree, (data, r), 'sphere', nproc)
    log.info('parallel brutal sphere finished')

    tree = BuildTree(data, 'kdtree')
    knn_kd_s = NNSearch(tree, (data, K), 'knn', 1)
    log.info('sequtial kdtree knn finished')
    knn_kd_p = NNSearch(tree, (data, K), 'knn', nproc)
    log.info('parallel kdtree knn finished')
    snn_kd_s = NNSearch(tree, (data, r), 'sphere', 1)
    log.info('sequtial kdtree sphere finished')
    snn_kd_p = NNSearch(tree, (data, r), 'sphere', nproc)
    log.info('parallel kdtree sphere finished')

    test(eq(sort(knn_br_s[2]), sort(knn_br_p[2])), 
         'parallel brutal knn')
    test(eq(sort(snn_br_s[2]), sort(snn_br_p[2])), 
         'parallel brutal snn')

    test(eq(sort(knn_kd_s[2]), sort(knn_kd_p[2])), 
         'parallel kdtree knn')
    test(eq(sort(snn_kd_s[2]), sort(snn_kd_p[2])), 
         'parallel kdtree snn')

    knn_err_ratio = 1.0*sum(fabs(knn_br_s[2]-knn_kd_s[2]) > 1e-5)/knn_br_s.shape[1]
    print 'KNN error ratio: %0.2f%%' % (knn_err_ratio*100)
    test(knn_err_ratio < 0.05, 'kdtree knn')

    snn_err_ratio = 1.0*fabs(snn_br_s.shape[1]-snn_kd_s.shape[1])/snn_br_s.shape[1]
    print 'SNN error ratio: %0.2f%%' % (snn_err_ratio*100)
    test(snn_err_ratio < 0.05, 'kdtree snn')
