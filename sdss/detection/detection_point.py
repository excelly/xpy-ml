# detection anomalies from SDSS using global PCA method

from ex import *

from feature import GetFeatures
import sdss_info as sinfo
from detector import *
import report

def usage():
    print('''
get the anomaly scores using global pca method

python --feature --scorer [--nproc={number of parallel processes}]
''')
    sys.exit(1)

custom_flags={
    1: 'star',
    2: 'galaxy',
    3: 'quasar'
}

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['nproc=', 'feature=', 'scorer='])

    nproc=int(opts.get('--nproc', 1))
    feature_names=opts.get('--feature', 'Spectrum')
    scorer=opts.get('--scorer', 'pca:accum_err:0.98').lower()

    output_dir='./detection_point/'
    MakeDir(output_dir)

    tag="[{0}][{1}]".format(feature_names, scorer)
    log.info('Run name: {0}'.format(tag))

    scorer, method, param = scorer.split(':')[:3]

    # get the feature
    feature, info = GetFeatures(feature_names, nproc = nproc)

    # scoring
    if scorer == 'pca':
        E = float(param)
        scores = PCAAnomalyScore(feature, feature, E, method)
    elif scorer == 'knn':
        K = int(param)
        scores = KNNAnomalyScore(feature, feature, K, method, nproc)
    elif scorer == 'mmf':
        rk = int(param)
        scores = MMFAnomalyScore(feature, feature, rk, method)[0]
    else:
        raise ValueError('unknown scorer')

    info['scores'] = scores
    # add the run id
    info['run_id']= sinfo.GetDetectionRunID(feature_names, scorer+'_'+method, custom_flags[info['spec_cln'][0]])
    
    output_file="{0}/score_{1}.pkl".format(output_dir, tag)
    SavePickle(output_file, info)

    # write the report
    html_an, html_all=report.GenReportIndividual(
        info['specObjID'], info['scores'], info['rdz'])

    SaveText('{0}/report_point_{1}_abnormal.html'.format(output_dir,tag), html_an)
    SaveText('{0}/report_point_{1}_all.html'.format(output_dir,tag), html_all)
