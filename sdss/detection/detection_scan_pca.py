import sys
import os
import logging as log
import numpy as np
import multiprocessing as mp

from ex.common import *
from ex.ioo import *
from ex.plott import *

from ex.geo.kdtree import KDTree

import utils

class SDSSTree(KDTree):
    pass

class AttributeScore:
    '''a class that provide minimum bounding box for each node in
    kdtree.
    '''

    def __init__(self, scores):
        self.scores=scores

    def SetAttribute(self, node, children=None):
        if children is None:
            idx=node.idx
            ss=self.scores[idx]
            node.n=len(idx)
            node.score_tot=ss.sum()
            node.score_avg=node.score_tot/node.n
        else:
            l, r=children

            node.idx=np.hstack((l.idx, r.idx))
            node.n=l.n + r.n
            node.score_tot=l.score_tot + r.score_tot
            node.score_avg=node.score_tot/node.n

def GetClusterFile(r):
    return "clusters_[{0:.5}].pkl".format(r)

def GetClusters(job):
    tree, location, r=job
    n=location.shape[1]
    clusters=[]
    for i in range(0, n, 1):
        clusters.append(tree.QueryRange((location[:,i], r**2), 'c'))
    SavePickles(GetClusterFile(r), [clusters])
    log.info('Clusters of radius {0} done'.format(r))

def GetClusterScore(cluster, score, method):
    if method=='mean':
        return score[cluster].mean()
    elif method=='median':
        return np.median(score[cluster])
    elif method=='count':
        return len(cluster)
    else:
        raise ValueError('unknown method')

if __name__ == '__main__':

    InitLog()

    input_file=sys.argv[1]
    data=LoadPickles(input_file)
    
    step=1
    score=data['score'][::step]
    target=data['target'][::step]
    pos=data['pos'][:,::step]
    z=data['z'][::step]
    dist=utils.ComovingDistance(z)
    xyz=data['xyz'][:,::step]
    spec_cln=data['spec_cln'][::step]
    n=len(score)

    location=pos
    rs=[2./60, 5./60, 10./60.]
#    location=xyz
#    rs=[0.1, 0.5, 1, 5]
    methods=['count', 'mean', 'median']

    # get the clusters
    tree=SDSSTree(location, 10)
    pool=mp.Pool(3)
    jobs=zip([tree]*len(rs), [location]*len(rs), rs)
    pool.map(GetClusters, jobs)

    n_anomaly=50
    for r in rs:
        clusters=LoadPickles(GetClusterFile(r))
        clusters=[cluster for cluster in clusters if len(cluster) > 4]

        for method in methods:
            tag="[{0:.5}][{1}]".format(r*1., method)

            cluster_scores=np.zeros(len(clusters))
            for i in range(len(clusters)):
                cluster_scores[i]=GetClusterScore(
                    clusters[i], score, method)

            html_an, html_all=utils.GenReportCluster(
                clusters, cluster_scores, r, None, 
                target, score, pos, dist, n_anomaly)

            SaveText('an_clusters_{0}_an.html'.format(tag), html_an)
            SaveText('an_clusters_{0}_all.html'.format(tag), html_all)

