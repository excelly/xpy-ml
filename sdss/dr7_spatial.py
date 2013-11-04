from ex import *
from ex.pp import *
from ex.nnsearch import KDTNNSearch as NNSearch
from ex.graph import *

import utils
from feature import GetFeatures

def usage():
    print('''
generate the spatial edges and clusters for dr7 data

python --coord={rdz, xyz} [--edge_thresh=10] [--cluster_thresh=1;3;5] [--nproc={number of parallel processes}]
''')
    sys.exit(1)

def GetEdges(coord_name, edge_thresh, nproc = 1):
    check(coord_name in ['rdz', 'xyz'], 'unknown coord type')

    etag = '[{0}][{1}]'.format(coord_name, edge_thresh)
    edge_file = 'edges_{0}.pkl'.format(etag)

    if os.path.exists(edge_file):
        log.info('Loading edges from {0}'.format(edge_file))

        data=LoadPickles(edge_file)
        edges=data['edges']
        spec_ids=data['spec_ids']
        rdz=data['rdz']
        xyz = data['xyz']
    else:
        log.info('Extracting edges from raw data')

        # get the locations
        feature, info = GetFeatures('Spectrum', nproc = nproc)
        del feature
        spec_ids = info['specObjID']
        rdz = info['rdz']
        xyz = utils.ConvertToCartesian(rdz[:,0], rdz[:,1], rdz[:,2])

        if coord_name == 'rdz':
            box = arr([[-10./60, -10./60, -edge_thresh],
                       [10./60, 10./60, edge_thresh]])
            rdd = rdz.copy()
            rdd[:,2] = utils.ComovingDistance(rdz[:,2])

            edges = NNSearch(rdd, [box + d for d in rdd], 'box', nproc, True)
        else:
            edges = NNSearch(xyz, (xyz, edge_thresh), 'sphere', nproc, True)

        SavePickle(edge_file, {'edges':edges, 'spec_ids':spec_ids, 'rdz':rdz, 'xyz':xyz})

    log.info('{0} edges found'.format(edges.shape[1]))
    return (edges, spec_ids, rdz, xyz)

def GetClusters(nNodes, edges = None, dist_thresh = None, cluster_size_thresh = 2):
    '''get clusters based on the neighborhood graph edges.

    this is done by finding connected components in the neighborhood
    graph. can be improved by finding maximum cliques.
    '''

    if edges is None:
        nNodes, edges, dist_thresh, cluster_size_thresh = nNodes

    # filter edge length
    filter = L2I(edges[2] <= dist_thresh)
    edges = edges[:,filter]
    log.info('{0} edges < {1}'.format(len(filter), dist_thresh))

    # find connected components
    G = ToGraph(edges, nNodes = nNodes)
    clusters = nx.connected_components(G)

    # filter by cluster size
    nc = len(clusters)
    clusters = [arr(c) for c in clusters if len(c) >= cluster_size_thresh]
    log.info('{0}/{1} clusters found /w size >= {2}'.format(len(clusters), nc, cluster_size_thresh))

    return clusters

if __name__ == '__main__':
    InitLog()

    opts=CmdArgs(sys.argv[1:], ['coord=', 'nproc=', 
                                'edge_thresh=', 'dist_thresh=', 'cluster_thresh='])
    nproc = int(opts.get('--nproc', 1))
    edge_thresh = int(opts.get('--edge_thresh', 5))
    dist_threshes = opts.get('--dist_thresh', "1;3;5")
    dist_threshes = [int(s) for s in dist_threshes.split(';')]
    coord_name = opts.get('--coord', 'xyz')

    edges, spec_ids, rdz, xyz = GetEdges(coord_name, edge_thresh, nproc)

    # construct clusters
    jobs = [(len(spec_ids), edges, t, 2) for t in dist_threshes]
    clusterss = ProcJobs(GetClusters, jobs, nproc)
    for ind in range(len(dist_threshes)):
        dist_thresh = dist_threshes[ind]
        ctag = '[{0}][{1}][{2}]'.format(coord_name, edge_thresh, dist_thresh)
        output_file = 'spatial_clusters_{0}'.format(ctag)
        clusters = clusterss[ind];

        SavePickle(output_file, {'clusters':clusters, 'spec_ids':spec_ids, 'rdz':rdz, 'xyz':xyz})

        clusters = [c + 1 for c in clusters]
        SaveMat(output_file, {'clusters':arr(clusters, dtype=np.object), 'spec_ids':spec_ids, 'rdz':rdz, 'xyz':xyz})
