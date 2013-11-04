from ex import *
from ex.ioo.FITS import FITS
import multiprocessing as mp

import sdss.utils as utils
import sdss_iii.settings as settings

def usage():
    print('''
transform the data into standard form

python proc_transform_data.py --input_files={input_files} --npixel=[500] --nproc=[1]
''')
    sys.exit(1)

def Filter(sf, vf):
    '''filter out bad objects
    '''

    n, dim = vf['spectrum'].shape

    #### filter by bad pixels
    sd = float32(1/np.sqrt(np.maximum(vf['invvar'], 1e-6)))
    filt_pix = (sd > settings.bad_pixel_std_thresh).sum(1) < dim*settings.bad_pixel_num_thresh

    #### filter by s2n
    # stars
    filt_star = sf['spec_cln'] == 1
    n_star = filt_star.sum()
    filt_star = reduce(AND, [filt_pix, filt_star, sf['s2n'] >= 3])
    # galaxy
    filt_gla = sf['spec_cln'] == 2
    n_gla = filt_gla.sum()
    filt_gla = reduce(AND, [filt_pix, filt_gla, sf['s2n'] >= 10])
    # qso
    filt_qso = sf['spec_cln'] == 3
    n_qso = filt_qso.sum()
    filt_qso = reduce(AND, [filt_pix, filt_qso, sf['s2n'] >= 10])

    log.info('''
Selected
%d / %d stars
%d / %d galaxies
%d / %d quasars
''' % (filt_star.sum(), n_star, 
       filt_gla.sum(), n_gla, 
       filt_qso.sum(), n_qso))

    return reduce(OR, [filt_star, filt_gla, filt_qso])

def ResampleSpectrum(y_np):
    y, npixel = y_np
    return utils.SplineResample(y, npixel)

def main(input_files, npixel=500, nproc=1):
    input_files = ExpandWildcard(input_files)
    MakeDir('./compact')
    log.info("Transforming {0} SDSS-III files using {1} processes. Output=./compact/".format(len(input_files), nproc))

    pool = mp.Pool(nproc)
    for input_file in input_files:
        output_file = "./compact/{0}.pkl".format(
            SplitFilename(input_file)[0])
        if os.path.exists(output_file): 
            log.info('Already processed {0}'.format(input_file))
            continue

        log.info("Processing %s -> %s" % (input_file,output_file))
        fits = FITS(input_file)

        vf = {'spectrum':   FixEndian(fits.HDUs[0].data),
              'invvar':     FixEndian(fits.HDUs[4].data)}
        log10_wl = FixEndian(fits.HDUs[3].data)

        sf = dict([(name, FixEndian(fits.HDUs[1].data.field(name))) 
                   for name in fits.HDUs[1].data.names])
        del sf['length']
        sf['mag'] = FixEndian(fits.HDUs[2].data)
        sf['spec_cln'] = arr(EncodeList(
                [c.strip().lower() for c in sf['class']], 
                settings.spec_cln_code.keys(), 
                settings.spec_cln_code.values()))
        sf['PMF'] = utils.PMF_S2N(sf['plate'],sf['mjd'],sf['fiber'])
        sf['stamp'] = zeros(len(vf['spectrum']), dtype = np.int64)
        sf['stamp'][:] = fits.HDUs[1].header['stamp']
        log.info("The following scalar features found: \n{0}".format(
                sf.keys()))

        filt = Filter(sf, vf)
        for key in sf.keys():
            sf[key] = sf[key][filt]
        for key in vf.keys():
            vf[key] = vf[key][filt]
        log.info("%d / %d objects left after filtering" % (
                filt.sum(), filt.size))

        log.info('Resampling %d spectra %d -> %d...'%(
                len(vf['spectrum']), vf['spectrum'].shape[1], npixel))
        jobs = [(spec, npixel) for spec in vf['spectrum']]
        spectrum = pool.map(ResampleSpectrum, jobs)

        log.info('Resampling %d invvar...'%len(vf['invvar']))
        jobs = [(iv, npixel) for iv in vf['invvar']]
        invvar = pool.map(ResampleSpectrum, jobs)
        log10_wl = linspace(log10_wl.min(), log10_wl.max(), npixel)

        # from ex.plott import *
        # h = figure();
        # subplot(h,211); plot(vf['spectrum'][0])
        # subplot(h,212); plot(spectrum[0])
        # show()
        vf['spectrum'] = spectrum
        vf['invvar'] = invvar

        log.info('Saving %s...'%output_file)
        SavePickle(output_file, {'SF': sf, 'VF': vf, 
                                 'log10_wl': log10_wl})

        fits.Close()
    

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], 
                   ['nproc=','input_files=','npixel='], 
                   usage)

    input_files = opts.get('--input_files')
    nproc = int(opts.get('--nproc', 1))
    npixel = int(opts.get('--npixel', 500))

    main(input_files, npixel, nproc)
