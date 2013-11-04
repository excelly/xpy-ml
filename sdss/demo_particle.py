from ex.common import *
from ex.ioo import *
import ex.geo.kdtree as kdtree
import ex.ml.util as emu
import ex.array as ea
from ex.plott import *
from random import random as rand

import networkx as nx

import sdss.detector as detector

def GetClusters(nNodes, edges, size_thresh=3):
    '''get clusters based on the neighborhood graph edges.

    this is done by finding connected components in the neighborhood
    graph. can be improved by finding maximum cliques.
    '''

    # find connected components
    G=nx.Graph()
    G.add_nodes_from(range(nNodes))
    G.add_edges_from(zip(edges[:,0], edges[:,1]))
    clusters=nx.strongly_connected_components(G)

    # filter
    clusters=[arr(c) for c in clusters if len(c) >= size_thresh]

    return clusters

def usage():
    print('''
python demo_particle.py --input={data file, should have a header} --neighbor_size={size of the e-ball}, --min_cluster_size={fof minimum size} [--normalized={if the histogram is normalized}] --poolsize={number of parallel processes}] [--K={number of neighbors when doing anomaly detection}] [--aggregate_time=0]
''')
    sys.exit(1)

if __name__=='__main__':
    InitLog(log.INFO)

    opts=getopt(sys.argv[1:], ['input=', 'poolsize=', 'neighbor_size=', 'min_cluster_size=', 'normalized=', 'aggregate_time='], 
                usage)

    input=opts['--input']
    neighbor_size=float(opts.get('--neighbor_size', 10))
    min_cluster_size=int(opts.get('--min_cluster_size',3))
    normalized=int(opts.get('--normalized', 0))
    poolsize=int(opts.get('--poolsize', 1))
    K=int(opts.get('--K', 1))
    aggregate_time=int(opts.get('--aggregate_time', 0))

    mat=ReadMatrixTxt(input, ',', np.float32)[1]
    timestamps=np.sort(uniqueInt(mat[:,0]))
#    timestamps=timestamps[:10]
    lims=[mat[:,1].min() - 10, mat[:,1].max() + 10, mat[:,2].min() - 10, mat[:,2].max() + 10]
    codebook=uniqueInt(mat[:, -1].astype(np.int32))
    ncode=len(codebook)
    log.info('Timestamps: {0}'.format(timestamps))
    log.info('Codebook: {0}'.format(codebook))

    clusters_time=[]
    hists_time=[]

    for i in range(len(timestamps)):
        ts=timestamps[i]
        log.info('Processing time step {0}'.format(ts))
        data=mat[mat[:,0] == ts, 1:]

        coord=data[:, :-1]
        n, dim=coord.shape
        vel=EncodeArray(data[:,-1].astype(np.int32), codebook)

        edges, dists=emu.GetNeighborGraph(coord, neighbor_size, 'ball-s', poolsize)
        clusters=GetClusters(n, edges, min_cluster_size)
        ncluster=len(clusters)

        hists=np.zeros((ncluster, ncode), dtype=np.float32)
        for i in range(ncluster):
            accumarray(vel[clusters[i]], base=hists[i])

        clusters_time.append(clusters)
        hists_time.append(hists)

    if normalized:
        hists_time=[Normalize(h, 's1', 'row')[0] for h in hists_time]

    if aggregate_time:
        hists_agg=np.vstack(hists_time)

    fig=figure()
    for i in range(len(timestamps)):
        ts=timestamps[i]
        print "-- Time step: {0}".format(ts)
        data=mat[mat[:,0] == ts, 1:]

        coord=data[:, :-1]
        n, dim=coord.shape
        vel=EncodeArray(data[:,-1].astype(np.int32), codebook)
                   
        # plot the points
        subplot(fig, 131);cla()
        scatter(coord[:,0], coord[:,1], 20, vel)
        axis(lims)

        clusters=clusters_time[i]
        ncluster=len(clusters)

        if ncluster < 2:
            continue

        hists=hists_time[i]
    
        # KNN detection
        if aggregate_time:
            scores=detector.KNNAnomalyScore(hists, hists_agg, K, 'mean_dist', True, poolsize)
        else:
            scores=detector.KNNAnomalyScore(hists, hists, K, 'mean_dist', True, poolsize)

        sidx=np.argsort(scores)[::-1]
        scores=[scores[sidx[i]] for i in range(ncluster)]
        clusters=[clusters[sidx[i]] for i in range(ncluster)]

        # plot the clusters
        ii=[]
        cscore=[]
        cid=[]
        ccenter=np.zeros((ncluster, 2), dtype=data.dtype)
        for i in range(ncluster):
            c=clusters[i]
            ii.extend(c)
            cscore.extend([scores[i]]*len(c))
            cid.extend([rand()]*len(c))
            ccenter[i]=coord[c].mean(0)
        ii=arr(ii)
        cscore=arr(cscore)
        cid=arr(cid)

        subplot(fig, 132);cla()
        scatter(coord[ii,0], coord[ii,1], 20, cid)
        scatter(ccenter[:,0], ccenter[:,1], 50, 'k')
        axis(lims)
        print "Time step {0} clusters are:".format(ts)
        for i in range(ncluster):
            print "** Score={0:.3}, Size={1}, Centroid={2}".format(
                scores[i], len(clusters[i]), ccenter[i])

        subplot(fig, 133);cla()
        scatter(coord[ii,0], coord[ii,1], 20, cscore)
        axis(lims)
        draw()
        pause()
