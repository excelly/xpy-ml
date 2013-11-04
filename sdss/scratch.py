# clustering the sdss data

from ex.common import *
from ex.io.common import *
import ex.array as ea
import ex.pp.mr as mr
import ex.ml.alg as ml
from ex.plott import *

import utils
import sdss_info as sinfo
import report

class ClusteringReducer(mr.BaseReducer):
    '''clustering a random subset of the data set and apply pca if specified.
    '''

    def __init__(self, feature, n_clusters, sample_rate=1, pca_model=None):
        mr.BaseReducer.__init__(self, "DR7 Clustering", True)

        self.feature=feature
        self.Feature=eval('utils.' + feature)
        self.sample_rate=sample_rate
        self.pca_model=pca_model
        self.n_clusters=n_clusters

    def Reduce(self, key, vals):
        input_file=vals[0]

        data=LoadPickles(input_file)
        feature=self.Feature(data)

        # sampling
        if self.sample_rate < 1:
            filter=np.random.rand(feature.shape[0]) <= self.sample_rate
            feature=feature[filter]
            log.debug('{0}/{1} samples selected'.format(feature.shape[0], len(filter)))

        if self.pca_model is not None:
            feature=pca_model.Project(feature)
            log.debug('Feature dimension reduced from {0} to {1}'.format(
                    pca_model.Dim, feature.shape[1]))
            
        log.info("Gathered {0} x {1} samples from {2}.".format(
                feature.shape[0], feature.shape[1], input_file))
        
        return feature

    def Aggregate(self, pairs):
        keys, samples=unzip(pairs)

        samples=np.vstack(samples)
        log.info('Start clustering N={0}, Dim={1}, K={2}.'.format(
                samples.shape[0], samples.shape[1], self.n_clusters))
        centers, distortion=ml.KML(samples, self.n_clusters, maxIter=100)
        log.info('Clustering finished. Final distortion = {0}'.format(distortion))

        return (centers, distortion)

class QuantizationReducer(mr.BaseReducer):
    '''quantize samples using given centers
    '''

    def __init__(self, feature, centers, pca_model=None):
        mr.BaseReducer.__init__(self, "DR7 Quantization", True)

        self.feature=feature
        self.Feature=eval('utils.' + feature)
        self.centers=centers
        self.pca_model=pca_model

    def Reduce(self, key, vals):
        input_file=vals[0]

        data=LoadPickles(input_file)
        feature=self.Feature(data)

        if self.pca_model is not None:
            feature=pca_model.Project(feature)
            log.debug('Feature dimension reduced from {0} to {1}'.format(
                    pca_model.Dim, feature.shape[1]))

        cluster_id, dists=ml.NNClassify(feature, self.centers)
        
        ra=data['SF']['RAOBJ']
        dec=data['SF']['DECOBJ']
        spec_id=data['SF']['specObjID']
        id=data['ID']
        
        return {'id':id, 'spec_id':spec_id, 'cluster_id':cluster_id, 'dists':dists,
                'ra':ra, 'dec':dec, 'feature':feature}

    def Aggregate(self, pairs):
        keys, results=unzip(pairs)

        id=AssembleVector(results, 'id')
        spec_id=AssembleVector(results, 'spec_id')
        cluster_id=AssembleVector(results, 'cluster_id')
        dists=AssembleVector(results, 'dists')
        ra=AssembleVector(results, 'ra')
        dec=AssembleVector(results, 'dec')
        pos=np.hstack((vec(ra), vec(dec)))
        feature=AssembleMatrix(results, 'feature')

        return {'id':id, 'spec_id':spec_id, 'cluster_id':cluster_id, 
                'dists':dists, 'pos':pos, 'centers':self.centers, 'feature':feature}

def usage():
    print('''
quantize the objects in dr7 data set. run this problem in the
top-level directory of the data set.

python dr7_quantization.py --dopca={0, 1} --feature={feature to use} --sample_rate={portion of data to use} --n_clusters={number of clusters} [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['poolsize=','dopca=','feature=','sample_rate=','n_clusters='])

    poolsize=opts.get('--poolsize', 1)
    dopca=1
    feature=opts.get('--feature', 'Spectrum')
    sample_rate=float(opts.get('--sample_rate', 1))
    n_clusters=int(opts.get('--n_clusters', 20))

    input_files=ExpandWildcard('./repaired/*.pkl')
    output_file='./quantization/quantization'

    run="[{0}][{1}][{2}][{3}]".format(
        feature, sample_rate, str(n_clusters).zfill(2), dopca)
    log.info('Clustering run name: {0}'.format(run))

    if dopca:
        import sdss.dr7_pca as dr7pca
        dummy, tag=dr7pca.DoPCA(None, feature, 0)
        pca_model_file="pca_model_{0}.pkl".format(tag)
        if os.path.exists(pca_model_file):
            log.info('Using existing PCA model from {0}'.format(pca_model_file))
            pca_model=ml.PCA(pca_model_file)
        else:
            pca_model=dr7pca.DoPCA(input_files, feature, 0, poolsize)[0]
            pca_model.Save(pca_model_file)
        pca_model.R=2 # !!
    else:
        pca_model=None

    # clustering
    reducer=ClusteringReducer(feature, n_clusters, sample_rate, pca_model)
    engine=mr.ReduceEngine(reducer, poolsize)
    centers, distortion=engine.Start(input_files)
    run+='[{0:.3}]'.format(distortion)

    reducer=QuantizationReducer(feature, centers, pca_model if dopca else None)
    engine=mr.ReduceEngine(reducer, poolsize)
    result=engine.Start(input_files)

    coord=result['feature'].T
    f=figure()
    scatter(coord[0], coord[1], s=20, c=result['cluster_id'])
    show()
    
    # SavePickle("{0}_{1}.pkl".format(output_file, run), result)

    # # generate report
    # spec_id=result['spec_id']
    # dists=result['dists']
    # cluster_id=result['cluster_id']
    # pos=result['pos']

    # sidx=np.argsort(dists)
    # dists=dists[sidx]
    # spec_id=spec_id[sidx]
    # cluster_id=cluster_id[sidx]
    # pos=pos[sidx]

    # idx=[]
    # for i in range(n_clusters):
    #     idx.append(find(cluster_id == i)[:3])
    # idx=np.hstack(idx)

    # html=report.GenReportIndividual(spec_id[idx], cluster_id[idx], pos[idx], len(idx))[0]
    # SaveText('report_{0}_{1}.html'.format(output_file, run), html)
