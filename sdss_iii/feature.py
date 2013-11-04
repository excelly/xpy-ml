from ex import *
from ex.pp import *
from ex.ml import *

import sdss_iii.settings as settings

############################# features

def Spectrum(data):
    f = data['VF']['spectrum']
    return float64(f)

def SpectrumS1(data):
    f = float64(Spectrum(data))
    return Normalize(f, 's1', 'row')[0]*f.shape[1]

class FeatureExtractor(mr.BaseReducer):
    '''gather the features for specified objects
    '''

    def __init__(self, feature_name, target_pmfs):
        mr.BaseReducer.__init__(self, 'SDSS III Feature Extractor', True)
        self.target_pmfs = target_pmfs
        self.Feature = eval(feature_name)

    def Reduce(self, key, vals):
        '''find the features in each compacted file
        '''

        input_file = vals[0]

        data = LoadPickles(input_file)
        feat = self.Feature(data)
        log.info("Feature {0} {1} from {2}.".format(
                self.Feature.__name__, feat.shape, input_file))

        output = data['SF']
        pmf = output['PMF']
        invvar = float64(data['VF']['invvar'])
        invvar[invvar < 1e-5] = 1e-5

        if self.target_pmfs is not None:
            filt = EncodeArray(pmf, self.target_pmfs) >= 0
        else:
            filt = ones(len(pmf), dtype=np.bool)

        output['X'] = float32(feat[filt])
        output['sd'] = float32(1/sqrt(invvar))
        for key in output.keys():
            output[key] = output[key][filt]

        return output

    def Aggregate(self, pairs):
        '''put the features together
        '''

        keys, results = unzip(pairs)

        output = {}
        for key in results[0].keys():
            if results[0][key].ndim == 1:
                output[key] = AssembleVector(results, key)
            else:
                output[key] = AssembleMatrix(results, key)

        return output

def ExtractFeature(feature_name, target_pmfs = None, data_files = './compact/*.pkl', nproc = 1):
    '''get the designated feature and related info from data
    '''

    input_files = ExpandWildcard(data_files)
    reducer = FeatureExtractor(feature_name, target_pmfs)
    engine = mr.ReduceEngine(reducer, nproc)
    result = engine.Start(input_files)

    return result

def GetFeatures(feature_names, data_files = './compact/*.pkl', nproc = 1):
    '''get the features from sdss data, and save it to
    feature_file. if file already exists then use the cached data.

    return (feature, info)
    feature is the design matrix
    '''

    feature_file = 'feature_%s.pkl' % feature_names

    if os.path.exists(feature_file):
        log.info('Loading feature {0} from {1}'.format(
                feature_names, feature_file))

        data = LoadPickles(feature_file)
        X = data['X']
        info = data['info']
    else:
        log.info('Extracting feature {0} from raw data'.format(
                feature_names))
        
        feature_names = feature_names.split('-')
        Xs = []
        for feature_name in feature_names:
            info = ExtractFeature(feature_name, None, data_files, nproc)
            Xs.append(info['X'])
        info['X'] = AssembleMatrix(Xs, by = 'col')

        SaveMat(feature_file.replace('.pkl', '.mat'), info)

        X = info['X']
        del info['X']
        SavePickle(feature_file, {'X':X, 'info':info})

    return (float64(X), info)

def GetRepairedFeatures(feature_names, cln, repairer = 'pca', 
                        data_files = './compact/*.pkl', nproc = 1):
    '''get the features from sdss data, and repair the bad pixels
    specify cln because feature must be repaired class by class

    return (feature, info)
    feature is the design matrix
    '''

    feature_file = 'feature_repaired_%d_%s_%s.pkl' % (cln, repairer, feature_names)

    if os.path.exists(feature_file):
        log.info('Loading repaired feature {0} from {1}'.format(
                feature_names, feature_file))

        data = LoadPickles(feature_file)
        X_repaired = data['X']
        info = data['info']
    else:
        log.info('Extracting feature {0} from class {1}, and repair using {2}'.format(feature_names, cln, repairer))
        X, info = GetFeatures(feature_names, data_files, nproc)

        filt = info['spec_cln'] == cln
        if not np.any(filt):
            return (None, None)
        else:
            X = X[filt]
            for key in info.keys():
                info[key] = info[key][filt]
        
        sd = info['sd']
        bad_mask = sd > settings.bad_pixel_std_thresh
        nbad = bad_mask.ravel().sum()
        log.info('Repairing %d (%f%%) bad pixels...'%(
                nbad, nbad*100.0/bad_mask.size))

        if repairer == 'rpca':
            X_clean = RPCA(X, lam = 1)[0]
        elif repairer == 'pca':
            pca = PCA.Train(X, 0.999)
            X_clean = pca.Reconstruct(pca.Project(X))
        else:
            raise ValueError('unknown repair method')
        info['repair'] = repairer

        X_repaired = X.copy()
        X_repaired[bad_mask] = X_clean[bad_mask]

        # import ex.plott as plt
        # fig = plt.figure()
        # n, dim = X_repaired.shape
        # counter = 0
        # for ind in range(n):
        #     if bad_mask[ind].sum() > 5:
        #         plt.cla()
        #         plt.plot(arange(dim), X_repaired[ind], 'r')
        #         plt.plot(arange(dim), X[ind], 'b')
        #         plt.plot(arange(dim), X_clean[ind]*0.8, 'g')
        #         plt.draw();pause()
        #         counter += 1
        #         if counter >= 10: break

        info['X'] = X_repaired
        SaveMat(feature_file.replace('.pkl', '.mat'), info)
        SaveMat(feature_file.replace('.pkl', '.ext'), 
                {'X':X, 'X_clean':X_clean, 'X_repaired':X_repaired})

        del info['X']
        SavePickle(feature_file, {'X':X_repaired, 'info':info})

    return (float64(X_repaired), info)

def usage():
    print('''
python feature.py

get common features
''')
    sys.exit(1)

def GetRPCARepair(args):
    feature_names, cln = args
    GetRepairedFeatures(feature_names, cln, 'rpca')

def main():
    log.info('Getting features...')

    GetFeatures('Spectrum')
    GetFeatures('SpectrumS1')

    GetRepairedFeatures('Spectrum', 1, 'pca')
    GetRepairedFeatures('SpectrumS1', 1, 'pca')
    GetRepairedFeatures('Spectrum', 2, 'pca')
    GetRepairedFeatures('SpectrumS1', 2, 'pca')
    GetRepairedFeatures('Spectrum', 3, 'pca')
    GetRepairedFeatures('SpectrumS1', 3, 'pca')

    jobs = [('Spectrum',1), ('SpectrumS1',1),
            ('Spectrum',2), ('SpectrumS1',2),
            ('Spectrum',3), ('SpectrumS1',3)]
#    ProcJobs(GetRPCARepair, jobs, 6)

if __name__ == '__main__':
    InitLog()

    main()
