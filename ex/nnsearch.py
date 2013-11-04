from common import *
from ex.pp import *
import scipy.spatial as spa

_global_data = None
def _init_global(data):
    global _global_data
    _global_data = data

def BrutalKNN_1(pool, target = None):
    '''find the neighbors of target in pool. target is tuple (X, K)

    returns a 3 x #edges matrix. each column is (x, y, distance)
    '''

    if target is None: pool, target = pool
    if pool is None: pool = _global_data

    X, K = target
    Y = pool
    nx, ny = (X.shape[0], Y.shape[0])

    D = L2Dist(X, Y, False)
    sidx = argsort(D, 1)[:,:K]
    dists = hstack([D[i,sidx[i]] for i in range(nx)])
    dists[dists < 0] = 0

    edges = vstack((kron(arange(nx), ones(K)),
                    sidx.ravel(),
                    sqrt(dists)))
    return edges

def BrutalKNN_2(pool, target = None):
    if target is None: pool, target = pool
    if pool is None: pool = _global_data

    X, K = target
    Y = pool
    nx, ny = (X.shape[0], Y.shape[0])

    D = L2Dist(X, Y, False)
    kmin = kth(D, K)

    sidx = zeros((nx, K), dtype=int64)
    dists = zeros((nx, K))
    for ind in range(nx):
        d = D[ind]
        si = np.where(d <= kmin[ind])[0]
        ii = argsort(d[si])
        sidx[ind] = si[ii[:K]]
        dists[ind] = d[sidx[ind]]
    dists[dists < 0] = 0

    edges = vstack((kron(arange(nx), ones(K)),
                    sidx.ravel(),
                    sqrt(dists.ravel())))
    return edges

def BrutalSNN_1(pool, target = None):
    '''find neighbors of target in pool. target is tuple (X, radius)

    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''

    if target is None: pool, target = pool
    if pool is None: pool = _global_data

    X, r = target
    Y = pool
    nx, ny = (X.shape[0], Y.shape[0])

    D = L2Dist(X, Y, False)
    F, T = (D <= r**2).nonzero()
    dists = D[(F, T)]
    dists[dists < 0] = 0
    dists = sqrt(dists)
    
    return vstack((F, T, dists))

def BrutalNNSearch(pool, target, method='knn', nproc=1, verbose=False):
    '''find neighbors of target in Y.
    method can be 'knn' or 'sphere'
    if knn, then target is (X, K)
    if sphere, then target is (X, radius)
    
    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''
    
    check(method in ['knn', 'sphere'], 'unknown method')

    X, param = target
    Y = pool

    if verbose:
        log.info('Brutally searching {0}-NN for {1} from {2} {3}-D points using {4} processes'.format(
                method, len(X), Y.shape[0], Y.shape[1], nproc))

    func = BrutalKNN_2 if method == 'knn' else BrutalSNN_1

    max_mem = 500 # megabytes
    nchunk = ceil(len(Y)*len(X)*8.0/1024/1024/max_mem)
    nchunk = max(nchunk, nproc)

    X_chunks = Partition(X, n_chunk = nchunk)
    sizes = arr([len(chunk) for chunk in X_chunks])
    jobs = [(None, (chunk, param)) for chunk in X_chunks]
    results = ProcJobs(func, jobs, nproc, _init_global, Y)

    if len(results) > 1:
        for ind in range(1, len(results)):
            results[ind][0] += sizes[:ind].sum()
        result = hstack(results)
    else:
        result = results[0]

    return MakeCont(result)

def KDTKNN_1(tree, target = None):
    '''find neighbors of target in tree. target is tuple (X, K)

    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''

    if target is None: tree, target = tree
    if tree is None: tree = _global_data

    X, K = target
    nx, dim = X.shape
    dists, idx = tree.query(X, K)

    edges = vstack((kron(arange(nx), ones(K)),
                    idx.ravel(), 
                    dists.ravel()))
    return edges

def KDTSNN_1(tree, target = None):
    '''find neighbors of target in tree. target is tuple (X, radius)
    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''

    if target is None: tree, target = tree
    if tree is None: tree = _global_data

    X, r = target
    Y = tree.data
    lidx = tree.query_ball_point(X, r)
    
    edges = [None]*len(lidx)
    for ind in range(len(lidx)):
        idx = lidx[ind]
        edges[ind] = vstack((
                ones(len(idx))*ind,
                idx,
                sqrt(sos(Y[idx] - X[ind], 1))
                ))
    edges = hstack(edges)
    return edges

def KDTNNSearch(tree, target, method = 'knn', nproc=1, verbose=False):
    '''find neighbors of target in Y using kdtree.
    if tree is not a KDTree but a data set, then a tree is built.
    method can be 'knn' or 'sphere' or 'box'
    if knn, then target is (X, K)
    if sphere, then target is (X, radius)
    
    returns a 3 x #edge matrix. each column is (x, y, distance)
    '''

    check(method in ['knn', 'sphere'], 'unknown method')
    
    X, param = target

    if verbose:
        log.info('KDTree searching {0}-NN for {1} {2}-D points using {3} processes'.format(method, len(X), X.shape[1], nproc))

    if not isinstance(tree, spa.cKDTree) and not isinstance(tree, spa.KDTree):
        if method == 'knn':
            tree = spa.cKDTree(tree, 10)
        else:
            tree = spa.KDTree(tree, 10)

    func = KDTKNN_1 if method == 'knn' else KDTSNN_1

    X_chunks = Partition(X, n_chunk = nproc)
    sizes = arr([len(chunk) for chunk in X_chunks])
    jobs = [(None, (chunk, param)) for chunk in X_chunks]
    results = ProcJobs(func, jobs, nproc, _init_global, tree)
    
    if len(results) > 1:
        for ind in range(1, len(results)):
            results[ind][0] += sizes[:ind].sum()
        result = hstack(results)
    else:
        result = results[0]

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

    leaf_size=10
    gridsize=50

    X, Y=MeshGrid(range(gridsize), range(gridsize))

    data=float32(hstack((col(X), col(Y))))

    nproc = 2

    K = 5

    log.info('nnsearch test started')
    r_br_s = BrutalNNSearch(data, (data, K), 'knn', 1)
    log.info('sequtial brutal knn finished')
    r_br_p = BrutalNNSearch(data, (data, K), 'knn', nproc)
    log.info('parallel brutal knn finished')
    r_kd_s = KDTNNSearch(data, (data, K), 'knn', 1)
    log.info('sequtial kdtree knn finished')
    r_kd_p = KDTNNSearch(data, (data, K), 'knn', nproc)
    log.info('parallel kdtree knn finished')

    test(eq(sort(r_br_s[2]), sort(r_br_p[2])), 
         'parallel brutal knn')
    test(eq(sort(r_br_s[2]), sort(r_kd_s[2])), 
         'seq kdtree knn')
    test(eq(sort(r_br_s[2]), sort(r_kd_p[2])), 
         'parallel kdtree knn')

    r = 1.2
    r_br_s = BrutalNNSearch(data, (data, r), 'sphere', 1)
    log.info('sequtial brutal sphere finished')
    r_br_p = BrutalNNSearch(data, (data, r), 'sphere', nproc)
    log.info('parallel brutal sphere finished')
    r_kd_s = KDTNNSearch(data, (data, r), 'sphere', 1)
    log.info('sequtial kdtree sphere finished')
    r_kd_p = KDTNNSearch(data, (data, r), 'sphere', nproc)
    log.info('parallel kdtree sphere finished')

    test(eq(sort(r_br_s[2]), sort(r_br_p[2])), 
         'parallel brutal sphere')
    test(eq(sort(r_br_s[2]), sort(r_kd_s[2])), 
         'seq kdtree sphere')
    test(eq(sort(r_br_s[2]), sort(r_kd_p[2])), 
         'parallel kdtree sphere')

    test((r_kd_s[0] == 0).sum() == 3, 'kd sphere corner')
    test((r_kd_s[0] == 10).sum() == 4, 'kd sphere edge')
    test((r_kd_s[0] == 225).sum() == 5, 'kd sphere center')
