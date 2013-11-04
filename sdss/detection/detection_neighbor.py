# detection anomalies from SDSS using neighborhood

from ex import *
import ex.pp.mr as mr
from ex.ml import *

import utils
import detector
import report
import sdss_info as sinfo

class FeatureReducer(mr.BaseReducer):
    '''map each file to its anomaly score and embedding coordinates
    '''

    def __init__(self, output_dest, feature):
        mr.BaseReducer.__init__(self, "Global MMF feature reducer", True)

        self.output_dest=output_dest
        self.Feature=eval('utils.' + feature)

    def Reduce(self, key, vals):
        input_file=vals[0]

        log.info("Feature {0} from {1}.".format(self.Feature, input_file))
        data=LoadPickles(input_file)
        feature=self.Feature(data)
        n, dim=feature.shape

        ids=data['ID']
        specObjID=data['SF']['specObjID']
        bestObjID=data['SF']['bestObjID']

        ra=data['SF']['RAOBJ']
        dec=data['SF']['DECOBJ']
        z=data['SF']['Z']
        spec_cln=data['SF']['SPEC_CLN']

        return {'feature': feature, 'ID': ids,
                'ra': ra, 'dec': dec, 'z': z, 'spec_cln':spec_cln, 
                'specObjID': specObjID, 'bestObjID': bestObjID}

    def Aggregate(self, pairs):
        keys, results=unzip(pairs)

        feature=AssembleMatrix(results, 'feature')
        ID=AssembleVector(results, 'ID')
        pos=np.hstack((vec(AssembleVector(results, 'ra')), 
                       vec(AssembleVector(results, 'dec'))))
        z=AssembleVector(results, 'z')
        spec_cln=AssembleVector(results, 'spec_cln')
        specObjID=AssembleVector(results, 'specObjID')
        bestObjID=AssembleVector(results, 'bestObjID')

        return {'feature': feature, 'ID': ID, 'pos': pos, 'z':z, 'spec_cln':spec_cln, 'specObjID': specObjID, 'bestObjID': bestObjID}

def usage():
    print('''
get the anomaly scores using global mmf

python [--feature=Spectrum] [--K=3] [--method=mean_dist] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

custom_flags={
    1: 'star',
    2: 'galaxy',
    3: 'quasar'
}

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['K=', 'method=', 'poolsize=', 'feature='])

    poolsize=opts.get('--poolsize', 1)
    K=int(opts.get('--K', 3))
    feature=opts.get('--feature', 'Spectrum')
    method=opts.get('--method', 'mean_dist').lower()

    output_dir='./local_nn/'
    MakeDir(output_dir)
    input_files=ExpandWildcard('./repaired/*.pkl')

    tag="[{0}][{1}][{2}]".format(feature, K, method)
    log.info('Run name: {0}'.format(tag))

    # extract feature
    reducer=FeatureReducer(output_dir, feature)
    engine=mr.ReduceEngine(reducer, poolsize)
    result=engine.Start(input_files)
    result['RunID']=sinfo.GetDetectorRunID(feature, 'nn_{0}'.format(method.lower()), custom_flags[result['spec_cln'][0]])

    # run MMF
    scores=detector.KNNAnomalyScore(result['feature'], result['feature'], K, method)
    del result['feature']

    result['scores']=scores
    output_file="{0}/score_{1}.pkl".format(output_dir, tag)
    SavePickle(output_file, result)

    html_an, html_all=report.GenReportIndividual(
        result['specObjID'], result['scores'], result['pos'])
    SaveText('{0}/report_local_nn_{1}_abnormal.html'.format(output_dir,tag), html_an)
    SaveText('{0}/report_local_nn_{1}_all.html'.format(output_dir,tag), html_all)
