from ex import *
from ex.ml import *
from feature import GetFeatures

def DoPCA(feature_names, nproc = 1):
    model_file = 'pca_model_[{0}].pkl'.format(feature_names)

    if os.path.exists(model_file):
        log.info('Loading PCA model from {0}'.format(model_file))
        model = PCA()
        model.Load(model_file)
    else:
        log.info('Training PCA model')

        X, info = GetFeatures(feature_names)
        model = PCA.Train(X)
        model.Save(model_file)
        model.Save(model_file.replace('.pkl','.mat'))
    
    return model

def usage():
    print('''
do pca for specified feature

python proc_pca.py --nproc=[1]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], 
                   ['nproc='], usage)

    # todo: distributed and online computation
    
    nproc = int(opts.get('--nproc', 1))

    model = DoPCA('Spectrum', nproc)
    model.Plot()

    # repair data

    model = DoPCA('SpectrumS1', nproc)
    model.Plot()

    show()
