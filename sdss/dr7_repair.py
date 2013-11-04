# repair the bad pixels in spectrums

from ex import *
import ex.pp.mr as mr
from ex.ml import *
from ex.plott import *

import settings

class RepairMapper(mr.BaseMapper):
    '''map each file to repair the bad pixels
    '''

    def __init__(self, output_dest, pca_spectrum, pca_continuum):
        mr.BaseMapper.__init__(self, "Repair Mapper", output_dest)

        self.pca_spectrum = pca_spectrum
        self.pca_continuum = pca_continuum

    def Map(self, key, val):
        input_file = val
        output_file = "{0}/{1}.pkl".format(
            self.output_dest, SplitFilename(input_file)[0])
        log.info("Repairing {0} -> {1}".format(
                input_file, output_file))

        data = LoadPickles(input_file)
        
        spectrum = data['VF']['spectrum']
        continuum = data['VF']['continuum']
        mask = (data['VF']['mask'] & settings.bad_mask) > 0
        n, dim = spectrum.shape

        # use continuum to replace spectrum
        for i in range(n):
            spectrum[i, mask[i,:]] = continuum[i, mask[i,:]]

        P = pca_spectrum.Project(spectrum)
        rs = pca_spectrum.Reconstruct(P)

        P = pca_continuum.Project(continuum)
        rc = pca_continuum.Reconstruct(P)

        spectrum_src = spectrum.copy()
        continuum_src = continuum.copy()

        # use pca reconstruct to replace spectrum
        for i in range(n):
            spectrum[i, mask[i,:]] = rs[i, mask[i,:]]
            continuum[i, mask[i,:]] = rc[i, mask[i,:]]

        # figure()
        # for i in range(n):
        #     cla()
        #     plot(range(dim),spectrum[i],'b',range(dim),spectrum_src[i],'r')
        #     draw()
        #     pause()

        data['VF']['spectrum'] = spectrum
        data['VF']['continuum'] = continuum

        SavePickle(output_file, data)

        return output_file

def usage():
    print('''
repair bad pixels in the spectrum and the continuum

python [--nproc = {number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], ['nproc='], usage)
    nproc = int(opts.get('--nproc', 1))

    output_dir = './repaired/'
    input_files = ExpandWildcard('./compact/*.pkl')
    MakeDir(output_dir)

    # train the pca models
    import sdss.dr7_pca as dr7pca
    dummy, tag = dr7pca.DoPCA(None, 'Spectrum', True)
    pca_file = "{0}_{1}.pkl".format('pca_repair', tag)
    if os.path.exists(pca_file):
        log.info('Using existing PCA model from {0}'.format(pca_file))
        pca_spectrum = PCA(pca_file)
    else:
        pca_spectrum, tag = dr7pca.DoPCA(
            input_files, 'Spectrum', True, nproc)
        pca_spectrum.Save(pca_file)

    dummy, tag = dr7pca.DoPCA(None, 'Continuum', False)
    pca_file = "{0}_{1}.pkl".format('pca_repair', tag)
    if os.path.exists(pca_file):
        log.info('Using existing PCA model from {0}'.format(pca_file))
        pca_continuum = PCA(pca_file)
    else:
        pca_continuum, tag = dr7pca.DoPCA(
            input_files, 'Continuum', False, nproc)
        pca_continuum.Save(pca_file)

    # adjust the dimension to use
    pca_spectrum.AdjustDim(0.95)
    pca_continuum.AdjustDim(0.95)

    mapper = RepairMapper(output_dir, pca_spectrum, pca_continuum)
    engine = mr.MapEngine(mapper, nproc)
    outputs = engine.Start(input_files)

    log.info('{0} files repaired'.format(len(outputs)))
