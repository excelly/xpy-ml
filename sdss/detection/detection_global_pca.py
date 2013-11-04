# detection anomalies from SDSS using global PCA method

from ex import *
import ex.pp.mr as mr
from ex.ml import *

import utils
import detector
import report
import sdss_info as sinfo

class ScoreReducer(mr.BaseReducer):
    '''map each file to its anomaly score and embedding coordinates
    '''

    def __init__(self, output_dest, pca_model, feature, score_type):
        mr.BaseReducer.__init__(self, "Global PCA detetor", True)

        self.output_dest=output_dest
        self.pca_model=pca_model
        self.Feature=eval('utils.' + feature)
        self.score_type=score_type

    def Reduce(self, key, vals):
        input_file=vals[0]

        output_file="{0}/{1}_score.pkl".format(
            self.output_dest, SplitFilename(input_file)[0])
        log.info("Scoring {0} -> {1} using <{2}>. Feature {3}.".format(
                input_file, output_file, score_type, self.Feature))

        data=LoadPickles(input_file)
        
        feature=self.Feature(data)
        n, dim=feature.shape

        embedding=self.pca_model.Project(feature, 3)
        scores=detector.PCAAnomalyScore(self.pca_model, feature, score_type)
        ids=data['ID']
        specObjID=data['SF']['specObjID']
        bestObjID=data['SF']['bestObjID']

        ra=data['SF']['RAOBJ']
        dec=data['SF']['DECOBJ']
        z=data['SF']['Z']
        spec_cln=data['SF']['SPEC_CLN']

        SavePickle(output_file, 
                   {'embedding': embedding, 'scores': scores, 'ID': ids,
                    'ra': ra, 'dec': dec, 'z': z, 'spec_cln':spec_cln, 
                   'specObjID': specObjID, 'bestObjID': bestObjID})

        return output_file

    def Aggregate(self, pairs):
        keys, output_files=unzip(pairs)

        # read in all the results
        results=[]
        for output_file in output_files:
            results.append(LoadPickles(output_file))

        embedding=AssembleMatrix(results, 'embedding')
        scores=AssembleVector(results, 'scores')
        ID=AssembleVector(results, 'ID')
        pos=np.hstack((vec(AssembleVector(results, 'ra')), 
                       vec(AssembleVector(results, 'dec'))))
        z=AssembleVector(results, 'z')
        spec_cln=AssembleVector(results, 'spec_cln')
        specObjID=AssembleVector(results, 'specObjID')
        bestObjID=AssembleVector(results, 'bestObjID')

        result={'embedding': embedding, 'scores': scores, 'ID': ID, 
                'pos': pos, 'z':z, 'spec_cln':spec_cln, 
                'specObjID': specObjID, 'bestObjID': bestObjID}

        return result

def usage():
    print('''
get the anomaly scores using global pca method

python [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

custom_flags={
    1: 'star',
    2: 'galaxy',
    3: 'quasar'
}

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=', 'feature=', 'pca_energy=', 'score_type='])

    poolsize=opts.get('--poolsize', 1)
    feature=opts.get('--feature', 'Spectrum')
    score_type=opts.get('--score_type', 'accum_err')
    pca_energy=float(opts.get('--pca_energy', 0.95))

    output_dir='./global_pca/'
    MakeDir(output_dir)
    input_files=ExpandWildcard('./repaired/*.pkl')

    tag="[{0}][{1}{2}]".format(feature, score_type, int(100*pca_energy))
    log.info('Run name: {0}'.format(tag))

    # train the pca model
    import sdss.dr7_pca as dr7pca
    dummy, pca_tag=dr7pca.DoPCA(None, feature, 0)
    pca_model_file="{0}_{1}.pkl".format('pca_model', pca_tag)
    if os.path.exists(pca_model_file):
        log.info('Using existing PCA model from {0}'.format(pca_model_file))
        pca_model=PCA(pca_model_file)
    else:
        pca_model=dr7pca.DoPCA(input_files, feature, 0, poolsize)[0]
        pca_model.Save(pca_model_file)

    # scoring
    reducer=ScoreReducer(output_dir, pca_model, feature, score_type)
    engine=mr.ReduceEngine(reducer, poolsize)
    result=engine.Start(input_files)
    # remove temp score files
    os.system('rm {0}/*_score.pkl'.format(output_dir))

    # add the run id
    result['RunID']=sinfo.GetDetectorRunID(feature, 'pca_'+score_type, 
                                   custom_flags[result['spec_cln'][0]])
    
    output_file="{0}/score_{1}.pkl".format(output_dir, tag)
    SavePickle(output_file, result)

    # write the report
    html_an, html_all=report.GenReportIndividual(
        result['specObjID'], result['scores'], result['pos'])

    SaveText('{0}/report_global_pca_{1}_abnormal.html'.format(output_dir,tag), html_an)
    SaveText('{0}/report_global_pca_{1}_all.html'.format(output_dir,tag), html_all)
