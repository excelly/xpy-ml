# detection anomalous clusters using the bag of gaussian models. 

from ex import *
from ex.plott import *
from ex.ml import PCA
from ex.ml.bag_model import *
from ex.ml.gmm import *

from scipy.special import psi

import base
import detector
import report
from feature import GetFeatures

def usage():
    print('''
detection anomalous spatial clusters using bag-of-gaussian models

python --cluster_file={result of dr7_spatial.py} --feature_names={SpectrumS1} [--size_range={10-50}] [--model_penalty=1]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['nproc=', 'cluster_file=', 'feature_names=', 'size_range=', 'model_penalty='], 
                usage)

    nproc=int(opts.get('--nproc', 1))
    cluster_file = opts['--cluster_file']
    feature_names = opts.get('--feature_names', 'SpectrumS1')
    size_range=opts.get('--size_range', "20-50")
    size_range = [int(s) for s in size_range.split('-')]
    model_penalty = float(opts.get('--model_penalty', 1))

    output_dir='./cluster_bagmodel/'
    MakeDir(output_dir)

    tag='{0}[{1}][{2}-{3}][{4}]'.format(
        cluster_file.replace('.pkl', '').replace('spatial_clusters_', ''), 
        feature_names, size_range[0], size_range[1], model_penalty)
    log.info('Run name: {0}'.format(tag))

    # load the data
    cluster_data=LoadPickles(cluster_file)
    #{'clusters', 'spec_ids'}
    feature, info = GetFeatures(feature_names, nproc = 1)
    #info: ['bestObjID', 'rdz', 'spec_cln', 'specObjID', 'ID']
    spec_ids=info['specObjID']
    spec_cln=info['spec_cln']
    pos = hstack((info['pos'], col(info['z'])))
    # make sure the data are compatible
    check(spec_ids == cluster_data['spec_ids'], 'incompatible data')

    # pca
    log.info('Training PCA...')
    pca = PCA.Train(feature, 0.99)
    # figure()
    # pca.Visualize(feature[int64(linspace(0, len(feature)-1, 10000))])
    # pause()
    feature = pca.Project(feature, min(pca.R, 50))

    clusters = cluster_data['clusters']

    # filter clusters
    clusters=[c for c in clusters if len(c) >= size_range[0] and len(c) <= size_range[1]]
    log.info('{0} clusters found between size range {1}'.format(len(clusters), size_range))

    # make bag-of-gaussians data
    M = len(clusters)
    N = [len(c) for c in clusters]
    cN = cat(([0], cumsum(N)))
    npoint = cN[-1]

    X = zeros((npoint, feature.shape[1]))
    group_id = zeros(npoint, int32)
    for m in range(M):
        X[cN[m]:cN[m+1]] = feature[clusters[m]]
        group_id[cN[m]:cN[m+1]] = m

    ####### detection

    Ts = arange(3, 8)[::-1]
    Ks = arange(3, 10)[::-1]
    options = {'ntry':10, 'init':'kmeans', 'bic_coeff':model_penalty, 
               'epsilon':1e-3, 'maxIter':50, 'verbose':False, 'symmetric':True,
               'nproc':1, 'nproc_bic':nproc}

    # MGMM
    R_mgmm, L_mgmm, stat_mgmm = FitMGMM_BICSearch(X, group_id, Ts, Ks, options)
    print stat_mgmm
    T = int(stat_mgmm[argmax(stat_mgmm[:,-1]), 0])
    K = int(stat_mgmm[argmax(stat_mgmm[:,-1]), 1])
    log.info('T=%d, K=%d selected for MGMM.' % (T, K))

    pi, chi, mu, sigma, gama, phi = R_mgmm
    lnpdf = GaussianPDF(X, mu, sigma)
    l_mgmm = MGMMGroupLikelihood(group_id, lnpdf, R_mgmm)
    l_mgmm_true = MGMMGroupLikelihoodTruth(group_id, lnpdf, R_mgmm)
    log.info('Var likelihood = %g; True likelihood = %g' % (l_mgmm.sum(), l_mgmm_true.sum()))
    scores_mgmm = -l_mgmm_true
    rank_mgmm = argsort(scores_mgmm)[::-1]

    options['nproc'] = nproc
    options['nproc_bic'] = 1
    # GLDA
    R_glda, L_glda = FitGLDA(X, group_id, K, options)
    alpha, mu, sigma, gama, phi = R_glda
    lnpdf = GaussianPDF(X, mu, sigma)
    pg = psi(gama) - col(psi(gama.sum(1)))
    l_glda = GLDAGroupLikelihood(group_id, lnpdf, pg, R_glda)
    scores_glda = -l_glda
    rank_glda = argsort(scores_glda)[::-1]

    # GMM
    R_gmm, L_gmm = FitGMM(X, K, options)
    pi, mu, sigma = R_gmm
    lnpdf = GaussianPDF(X, mu, sigma)
    l_gmm = GMMLikelihood(lnpdf.T, R_gmm)
    l_gmm = accumarray(group_id, l_gmm, zeros(M))
    scores_gmm = -l_gmm
    rank_gmm = argsort(scores_gmm)[::-1]

    cluster_info = ['MGMM: {0} <br> GLDA: {1} <br> GMM: {2}'.format(rank_mgmm[i], rank_glda[i], rank_gmm[i]) for i in range(len(clusters))]
    html_an, html_all=report.GenReportCluster(clusters, scores_glda, spec_ids, pos, cluster_info, None, 20)
    SaveText('{0}/report_glda_{1}_anomaly.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_glda_{1}_all.html'.format(output_dir, tag), html_all)

    html_an, html_all=report.GenReportCluster(clusters, scores_gmm, spec_ids, pos, cluster_info, None, 20)
    SaveText('{0}/report_gmm_{1}_anomaly.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_gmm_{1}_all.html'.format(output_dir, tag), html_all)

    html_an, html_all=report.GenReportCluster(clusters, scores_mgmm, spec_ids, pos, cluster_info, None, 20)
    SaveText('{0}/report_mgmm_{1}_anomaly.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_mgmm_{1}_all.html'.format(output_dir, tag), html_all)

    scores_mgmm_v_glda = fabs(rank_mgmm - rank_glda)
    html_an, html_all=report.GenReportCluster(clusters, scores_mgmm_v_glda, spec_ids, pos, cluster_info, None, 20)
    SaveText('{0}/report_mgmm_v_glda_{1}_anomaly.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_mgmm_v_glda_{1}_all.html'.format(output_dir, tag), html_all)

    scores_mgmm_v_gmm = fabs(rank_mgmm - rank_gmm)
    html_an, html_all=report.GenReportCluster(clusters, scores_mgmm_v_gmm, spec_ids, pos, cluster_info, None, 20)
    SaveText('{0}/report_mgmm_v_gmm_{1}_anomaly.html'.format(output_dir, tag), html_an)
    SaveText('{0}/report_mgmm_v_gmm_{1}_all.html'.format(output_dir, tag), html_all)

    workspace = (l_gmm, l_glda, L_gmm, clusters, R_gmm, logsafe, l_mgmm_true, X, L_mgmm, group_id, npoint, cluster_file, L_glda, stat_mgmm, cluster_data, cN, scores_glda, R_mgmm, options, l_mgmm, pos, scores_gmm, model_penalty, N, Ks, info, Ts, tag, feature_names, R_glda, M, scores_mgmm, nproc, size_range, spec_ids, rank_mgmm, rank_glda, rank_gmm, T, K)
    SavePickle('{0}/workspace_{1}.pkl'.format(output_dir, tag), workspace)
