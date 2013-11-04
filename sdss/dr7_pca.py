from ex import *
import ex.pp.mr as mr
from ex.ml import *
from ex.plott import *

import settings
import utils
import feature

class Reducer(mr.BaseReducer):
    '''get the pca model for compact dr7 data set
    '''

    def __init__(self, mask_bad, feature_name):
        mr.BaseReducer.__init__(self, 'DR7 PCA', True)
        self.mask_bad = bool(mask_bad)
        self.feature_name = feature_name

        if mask_bad:
            check(feature_name == 'Spectrum', 'unsupported')

    def Reduce(self, key, vals):
        '''return the mean and covariance for one plate
        '''

        input_file = vals[0]
        log.info("Processing input {0}".format(input_file))

        data = LoadPickles(input_file)
        Feature = eval('feature.' + self.feature_name)
        feat = Feature(data)
        n, dim = feat.shape
        
        if self.mask_bad:
            feat = utils.MaskFeature(feat, data['VF']['mask']);
            log.info('{0}/{1} bad pixels found.'.format(np.isnan(feat).sum(), n*dim))

            continuum = data['VF']['continuum']
            for i in range(n):
                idx = np.isnan(feat[i])
                feat[i, idx] = continuum[i, idx]

        # figure()
        # for i in range(n):
        #     cla()
        #     plot(np.arange(dim), feat[i,:])
        #     draw()
        #     pause()

        # exclude samples with missing values
        filter = np.isnan(feat).sum(1) == 0
        feat = feat[filter]
        log.info('{0}/{1} good samples found'.format(
                filter.sum(), len(filter)))

        return (n, feat.sum(0), mul(feat.T, feat))

    def Aggregate(self, pairs):
        '''return the total number of objects compacted
        '''

        results = [p[1] for p in pairs]
        log.info('Combining immediate results')
        n, mu, sigma = reduce(lambda d1, d2: [d1[i] + d2[i] for i in range(len(d1))], results)

        mu = col(mu/n)
        sigma = sigma/n - mul(mu, mu.T)

        pca_model = PCA.TrainCov(mu, sigma, n, 0.95)

        # pca_model.Plot()
        # draw()
        # pause()

        return pca_model

def DoPCA(input_files, feature_name = 'Spectrum', mask_bad = 0, nproc = 1):

    if input_files is not None:
        log.info("Doing PCA for {0} DR7 files using {1} processes.".format(len(input_files), nproc))
        log.info("Feature = {0}, Mask bad = {1}".format(feature_name, mask_bad))
    
        reducer = Reducer(mask_bad, feature_name)
        engine = mr.ReduceEngine(reducer, nproc)

        pca_model = engine.Start(input_files)
    else:
        pca_model = None

    tag = "[{0}][{1}]".format(feature_name, mask_bad)

    return (pca_model, tag)

def usage():
    print('''
get the pca model for a compact dr7 data set.

python dr7_pca.py --input={source data files} --output={model name} [--mask_bad=0] [--feature=spectrum] [--nproc={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog(log.INFO)

    opts = CmdArgs(sys.argv[1:], ['input=','output=','nproc=','mask_bad=','feature='], usage)

    input_files = ExpandWildcard(opts['--input'])
    output_file = opts.get('--output', 'pca_model')
    nproc = opts.get('--nproc', 1)
    mask_bad = opts.get('--mask_bad', False)
    feature_name = opts.get('--feature', 'Spectrum')

    pca_model, tag = DoPCA(input_files, feature_name, 0.95, mask_bad, nproc)
    
    output_file = '{0}_{1}.pkl'.format(output, tag)
    log.info('Output the PCA model to {0}'.format(output_file))
    pca_model.Save(output_file)
