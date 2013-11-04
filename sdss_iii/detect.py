from ex import *
from ex.pp import *
from ex.ml import *

import ex.nnsearch as nn
import ex.annsearch as ann

import sdss_iii.settings as settings
from sdss_iii.feature import GetRepairedFeatures
import sdss_iii.web_report.report as report

import sdss.detection.detector as detector

output_dir = './detection_results'
knn_nproc = 1

pca_E = 0.95

def Output(feature_names, det_name, method, scores, info):
    cln = info['spec_cln'][0]
    tag = '[{0}][{1}][{2}-{3}]'.format(cln,feature_names,det_name,method)
    log.info('Outputing %s' % tag)

    score_file = '{0}/scores_pad_{1}'.format(output_dir, tag)
    report_file = '{0}/report_pad_{1}'.format(output_dir, tag)
    run_id = settings.GetDetectionRunID(
        feature_names, '%s_%s'%(det_name, method), 
        settings.spec_cln_code_inv[cln])
    
    score_data = info;
    score_data['scores'] = scores
    score_data['run_id'] = run_id
    SavePickle(score_file + '.pkl', score_data)
    SaveMat(score_file + '.mat', score_data)
        
    html_an, html_all = report.GenPADReport(scores, info)
    SaveText(report_file + '_anomaly.html', html_an)
    SaveText(report_file + '_all.html', html_all)    

    return tag

def Detect_PCA(X, info, feature_names):
    pca = PCA.Train(X, pca_E)
    pca.R = min(50, max(2, pca.R))
    methods = ['rec_err', 'accum_err', 'dist', 'dist_out']
    for method in methods:
        scores = detector.PCAScore_Model(X, pca, method)
        Output(feature_names, 'pca', method, scores, info)

def Detect_Robust(X, info, feature_names):
    ############ use drmf to clean outliers
    L_rpca, sv_rpca = RPCA(X, 0.2)
    L_drmf, S_drmf = DRMF(X, 5, 0.05, {'init':L_rpca})

    ############ lr scores
    p = 10
    scores = sum(fabs(X - L_rpca)**p, 1)
    tag = Output(feature_names, 'rpca', 'aprx', scores, info)
    scores = sum(fabs(X - L_drmf)**p, 1)
    tag = Output(feature_names, 'drmf', 'aprx', scores, info)

    ############ still use pca for detection
    pca = PCA.Train(X - S_drmf) # remove outliers
    methods = ['rec_err', 'accum_err', 'dist', 'dist_out']
    for method in methods:
        scores = detector.PCAScore_Model(X, pca, method)
        Output(feature_names, 'drmf', method, scores, info)

    SaveMat('data_pad_[{0}][robust].mat'.format(feature_names),
            {'X':X,'L_rpca':L_rpca,'L_drmf':L_drmf,'S_drmf':S_drmf})

def Detect_KNN(X, info, feature_names, K = 10):
    scores, edges = detector.KNNScore(X, X, K, 'mean_dist', knn_nproc)
    tag = Output(feature_names, 'knn', 'mean_dist', scores, info)

    scores = detector.KNNScoreEdges(edges, 'max_dist')
    tag = Output(feature_names, 'knn', 'max_dist', scores, info)

    cln = info['spec_cln'][0]
    sim_type = 'l2'
    sim_file = 'similarity_%d_%dNN_%s_%s.pkl' % (
        cln, K, feature_names, sim_type)
    log.info('Saving similarities to %s' % sim_file)
    edges[2] = -edges[2]
    data = {'pairs':edges, 'pmf':info['PMF'],
            'feature':feature_names,'similarity':sim_type,'spec_cln':cln}
    SavePickle(sim_file, data)
    SaveMat(sim_file.replace('.pkl','.mat'), data)

def main(feature_names, cln, det_name):
    MakeDir(output_dir)

    X, info = GetRepairedFeatures(feature_names, cln, repairer = 'pca')
    if X is None: return

    if det_name == 'pca':
        Detect_PCA(X, info, feature_names)
    elif det_name == 'robust':
        Detect_Robust(X, info, feature_names)
    elif det_name == 'knn':
        Detect_KNN(X, info, feature_names)
    else:
        raise ValueError('unknown detector')

def DoDetection(args):
    main(args[0], args[1], args[2])

def usage():
    print('''
detect anomalies using PCA methods

python detect_pca.py --feature_names=[Spectrum] --detector=[pca] --nproc=[1]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], 
                   ['nproc=','feature_names=','detector='], 
                   usage)
    nproc = int(opts.get('--nproc', 1))
    feature_names = opts.get('--feature_names', 'Spectrum')
    det_name = opts.get('--detector', 'pca')

    MakeDir(output_dir)
    if det_name.lower() == 'all':
        jobs = [('Spectrum', 'pca'), 
                ('SpectrumS1', 'pca'), 
                ('Spectrum', 'robust'), 
                ('SpectrumS1', 'robust'), 
                ('Spectrum', 'knn'), 
                ('SpectrumS1', 'knn')]
    elif det_name.lower() == 'pca':
        jobs = [('Spectrum', 'pca'), 
                ('SpectrumS1', 'pca')]
    elif det_name.lower() == 'robust':
        jobs = [('Spectrum', 'robust'), 
                ('SpectrumS1', 'robust')]
    elif det_name.lower() == 'knn':
        jobs = [('Spectrum', 'knn'), 
                ('SpectrumS1', 'knn')]
        knn_nproc = nproc
        nproc = 1
    else:
        jobs = [(feature_names, det_name)]

    tmp = []
    for fn, det in jobs: tmp.extend([(fn, cln, det) for cln in (1,2,3)])
    jobs = tmp

    ProcJobs(DoDetection, jobs, nproc)
