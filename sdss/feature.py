from ex import *
import ex.pp.mr as mr

############################# features
def Color(data):
    f = AssembleMatrix((data['SF']['fiberMag_u'], 
                      data['SF']['fiberMag_g'], 
                      data['SF']['fiberMag_r'], 
                      data['SF']['fiberMag_i'], 
                      data['SF']['fiberMag_z']), by = 'row')

    return Normalize(f.T, 's1', 'row')[0]*f.shape[0]

def Mask(data):
    return data['VF']['mask']

def Continuum(data):
    f = data['VF']['continuum']
    return float64(f)

def Spectrum(data):
    f = data['VF']['spectrum']
    return float64(f)

def ContinuumS1(data):
    f = Continuum(data)
    return Normalize(f, 's1', 'row')[0]

def SpectrumS1(data):
    f = Spectrum(data)
    return Normalize(f, 's1', 'row')[0]

def ContinuumN1(data):
    f = Continuum(data)
    return Normalize(f, 'n1', 'row')[0]

def SpectrumN1(data):
    f = Spectrum(data)
    return Normalize(f, 'n1', 'row')[0]

def Lines(data):
    fs = data['LF'].values()
    f = float64(AssembleMatrix(fs, by = 'col'))
    f[f < -9000] = nan
    return f

def Separated(data):
    f = hstack((Lines(data), Continuum(data)))
    f = Normalize(f, 'm0v1', 'col')[0]
    return float64(f)

class FeatureExtractor(mr.BaseReducer):
    '''gather the features for specified objects
    '''

    def __init__(self, feature_name, target_spec_ids):
        mr.BaseReducer.__init__(self, 'Feature Extractor', True)
        self.target_spec_ids = None if target_spec_ids is None else int64(target_spec_ids)
        self.Feature = eval(feature_name)

    def Reduce(self, key, vals):
        '''find the features in each compacted file
        '''

        input_file = vals[0]
        data = LoadPickles(input_file)
        feat = self.Feature(data)
        log.info("Feature {0} {1} from {2}.".format(
                self.Feature.__name__, feat.shape, input_file))

        if 'MPF' in data.keys():
            mpf = data['MPF']
        else:
            m = data['SF']['mjd']
            p = data['SF']['plate']
            f = data['SF']['fiberID']
            mpf = [str(m[i]).zfill(5) + str(p[i]).zfill(4) + str(f[i]).zfill(3) for i in range(len(m))]
            mpf = arr(mpf)
        specObjID = data['SF']['specObjID']
        bestObjID = data['SF']['bestObjID']
        rdz = vstack((data['SF']['RAOBJ'],
                      data['SF']['DECOBJ'],
                      data['SF']['Z'])).T
        spec_cln = data['SF']['SPEC_CLN']

        if self.target_spec_ids is not None:
            filter = EncodeArray(specObjID, self.target_spec_ids) >= 0
        else:
            filter = ones(len(specObjID), dtype = np.bool)

        return {'feat':feat[filter], 
                'MPF':mpf[filter],
                'rdz':rdz[filter],
                'spec_cln':spec_cln[filter], 
                'specObjID':specObjID[filter], 
                'bestObjID':bestObjID[filter]}

    def Aggregate(self, pairs):
        '''put the features together
        '''

        keys, results = unzip(pairs)

        feat = AssembleMatrix(results, 'feat')
        mpf = AssembleVector(results, 'MPF')
        rdz = AssembleMatrix(results, 'rdz', by = 'row')
        spec_cln = AssembleVector(results, 'spec_cln')
        specObjID = AssembleVector(results, 'specObjID')
        bestObjID = AssembleVector(results, 'bestObjID')

        return {'feature': feat, 
                'rdz': rdz, 'spec_cln':spec_cln, 'MPF': mpf, 
                'specObjID': specObjID, 'bestObjID': bestObjID}

def ExtractFeature(feature, target_spec_ids = None, data_dir = './repaired/*.pkl', nproc = 1):
    '''get the designated feature and related info from data
    '''

    input_files = ExpandWildcard(data_dir)
    reducer = FeatureExtractor(feature, target_spec_ids)
    engine = mr.ReduceEngine(reducer, nproc)
    result = engine.Start(input_files)

    return result

def GetFeatures(feature_names, data_dir = './repaired/*.pkl', nproc = 1):
    '''get the features from sdss data, and save it to
    feature_file. if file already exists then use the cached data.

    return (feature, info)
    feature is the design matrix
    info is a dict of:
    ['bestObjID', 'rdz', 'spec_cln', 'specObjID', 'ID']
    '''

    feature_file = 'feature_%s.pkl' % feature_names

    if os.path.exists(feature_file):
        log.info('Loading feature {0} from {1}'.format(
                feature_names, feature_file))

        data = LoadPickles(feature_file)
        feat = data['feature']
        info = data['info']
    else:
        log.info('Extracting feature {0} from raw data'.format(
                feature_names))
        
        feature_names = feature_names.split('-')
        tmp = []
        for feature_name in feature_names:
            info = ExtractFeature(feature_name,
                                  None, data_dir, nproc)
            tmp.append(info['feature'])
            del info['feature']
        feat = AssembleMatrix(tmp, by = 'col')

        SavePickle(feature_file, {'feature':feat,
                                  'info':info})

        SaveMat(feature_file.replace('.pkl', '.mat'),
                {'feature':feat, 
                 'spec_ids':info['specObjID'], 
                 'MPF':info['MPF'],
                 'rdz':info['rdz'], 
                 'spec_cln':info['spec_cln']})

    return (feat, info)

def usage():
    print('''
get common features
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    log.info('Getting spectrum...')
    GetFeatures('Spectrum')

    log.info('Getting continuum...')
    GetFeatures('Continuum')

    log.info('Getting lines...')
    GetFeatures('Lines')
