# detection anomalous clusters using the histogram method. 

#1, quantize objects. 2, find spatial clusters. 3, for each spatial
#cluster, get the histogram of objects. 4, treat the histogram as the
#cluster feature and do anomaly detection.

from ex import *
from ex.plott import *
from ex.ml import *

import utils
import detector
import report

def usage():
    print('''
detection anomalous spatial clusters using quantization and histograms

python --edgefile={result of dr7_spatial_edges.py} --quantfile={result
of dr7_quantization.py} --dist_thresh={threshold of edge length}
--size_thresh={threshold of cluster size}
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=','edgefile=','quantfile=',
                               'dist_thresh=', 'size_thresh='], 
                usage)

    poolsize=int(opts.get('--poolsize', 1))
    edge_file=opts['--edgefile']
    quant_file=opts['--quantfile']
    dist_thresh=int(opts.get('--dist_thresh', 3))
    size_thresh=int(opts.get('--size_thresh', 5))

    output_dir='./cluster_histogram/'
    MakeDir(output_dir)

    otag='[{0}][{1}][{2}][{3}]'.format(os.path.basename(edge_file), os.path.basename(quant_file), dist_thresh, size_thresh)
    otag=otag.replace('.pkl', '')
    log.info('Run name: {0}'.format(otag))

    quant_data=LoadPickles(quant_file)
    # {'id':id, 'spec_id':spec_id, 'cluster_id':cluster_id, 
    # 'dists':dists, 'pos':pos, 'centers':self.centers}
    edge_data=LoadPickles(edge_file)
    #{'edges':edges, 'dists':dists}

    spec_id=quant_data['spec_id']
    pos=quant_data['pos']
    oid=quant_data['cluster_id']
    nCode=arguniqueInt(oid).size

    edges=EncodeArray(edge_data['edges'], spec_id)
    clusters=utils.GetClusters(len(spec_id), edges, edge_data['dists'], 
                              dist_thresh, size_thresh)

    # SavePickle('clusters.pkl', (clusters,))
    # clusters=LoadPickles('clusters.pkl')

    # remove really large clusters
    clusters=[c for c in clusters if len(c) <= 50]

    ncluster=len(clusters)
    features=np.zeros((ncluster, nCode), dtype=np.float32)
    for i in range(ncluster):
        accumarray(oid[clusters[i]], base=features[i])

    SaveMat('{0}/cluster_feature_{1}.mat'.format(output_dir, otag),
            {'features':features, 'clusters':arr(clusters, dtype=np.object),
             'spec_ids':spec_id, 'pos':pos})

    normalize=0
    tag="{0}[{1}]".format(otag, normalize)
    if normalize:
        features=Normalize(features, 's1', 'row')[0]

    # pca detection
    pca_model = PCA.Train(features, 0.95)
    scores=detector.PCAAnomalyScore(pca_model, features, 'accum_err')

    cluster_info=['Hist: {0}'.format(f) for f in features]
    object_info=['Class: {0}'.format(id) for id in oid]

    html_an, html_all=report.GenReportCluster(clusters, scores, spec_id, pos, cluster_info, object_info, 10)
    SaveText('{0}/report_PCA_{1}_abnormal.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_PCA_{1}_all.html'.format(output_dir, tag), html_all)
    
    # KNN detection
    K=3
    scores=detector.KNNAnomalyScore(features, K, 'max_dist', poolsize)

    html_an, html_all=report.GenReportCluster(clusters, scores, spec_id, pos, cluster_info, object_info, 10)
    SaveText('{0}/report_{1}NN_{2}_abnormal.html'.format(output_dir, K, tag), html_an)
    SaveText('{0}/report_{1}NN_{2}_all.html'.format(output_dir, K, tag), html_all)

    normalize=1
    tag="{0}[{1}]".format(otag, normalize)
    if normalize:
        features=Normalize(features, 's1', 'row')[0]

    # pca detection
    pca_model = PCA.Train(features, 0.95)
    scores=detector.PCAAnomalyScore(pca_model, features, 'accum_err')

    cluster_info=['Hist: {0}'.format(f) for f in features]
    object_info=['Class: {0}'.format(id) for id in oid]

    html_an, html_all=report.GenReportCluster(clusters, scores, spec_id, pos, cluster_info, object_info, 10)
    SaveText('{0}/report_PCA_{1}_abnormal.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_PCA_{1}_all.html'.format(output_dir, tag), html_all)
    
    # KNN detection
    K=3
    scores=detector.KNNAnomalyScore(features, K, 'max_dist', poolsize)

    html_an, html_all=report.GenReportCluster(clusters, scores, spec_id, pos, cluster_info, object_info, 10)
    SaveText('{0}/report_{1}NN_{2}_abnormal.html'.format(output_dir, K, tag), html_an)
    SaveText('{0}/report_{1}NN_{2}_all.html'.format(output_dir, K, tag), html_all)
