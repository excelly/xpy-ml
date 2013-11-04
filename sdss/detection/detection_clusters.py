# detection anomalous clusters in the data set

from ex import *
from ex.geo.common import *
from ex.ml import *

import utils

def ClusterFeature(cluster, features):
    '''fit a gaussian distribution for this cluster
    '''

    X=features[:, cluster]
    return (X.mean(1), X.std(1, ddof=1))

if __name__ == '__main__':
    InitLog(log.DEBUG)

    input_file=sys.argv[1]
    data=LoadPickles(input_file)
    # data is {'target': target, 'pos': pos, 'z':z, 'xyz': xyz, 'feature': feature, 'clusters': clusters}

    clusters=data['clusters']
    features=data['feature'].T
    pos=data['pos']
    n=features.shape[1]
    nc=len(clusters)
    r=4./60 # maximum is 10./60

    # normalize the feature
    log.debug('Normalizing features of size {0}...'.format(features.shape))
    features=Normalize(features, 's1', 'row')[0]
    features *= features.shape[0]

    # retouch the clusters
    for i in range(nc):
        cluster=clusters[i]
        center=pos[:, cluster[0]]
        pp=pos[:, cluster]
        filter=Inside(pp, (center, r**2), 'c')
        clusters[i]=cluster[filter]

    # reduce the features if using KNN method
    # log.debug('Reducing Dim...')
    # energy=0.9
    # U, L, M, R=ml.pca(features, energy)
    # features=mul(U[:, 0:min(R, 10)].T, features)
    # log.info('Dim={0} for {1} energy. Dim reduced to {2}'.format(
    #         R, energy, features.shape[0]))

    log.debug('Extracting cluster features...')
    cluster_thresh=3
    cs=[]
    ci=[]
    cf=[]
    for i in range(nc):
        if len(clusters[i]) > cluster_thresh:
            mu, sigma=ClusterFeature(clusters[i], features)
            cf.append(mu)
            cs.append(clusters[i])
    ci=arr(ci)
    cf=np.vstack(cf).T

    print cf.shape

    log.debug('Scoring clusters...')
    # pca detection
    U, L, M, R=ml.pca(cf, 0.95)
    pca_model={'U':U, 'L':L, 'M':M, 'R':R}
    score=utils.PCAAnomalyScore(pca_model, cf.T, 'accum_err')

    pp=mul(U[:, 0:R].T, cf);
    figure()
    scatter(pp[0,:], pp[1,:], c=score)
    show()

    html_an, html_all=utils.GenReportCluster(
        cs, score, r, None, data['target'], 
        -np.ones(n), data['pos'], data['z'])

    SaveText('clusters_mean_r{0:.5}_an.html'.format(r), html_an)
    SaveText('clusters_mean_r{0:.5}_all.html'.format(r), html_all)
