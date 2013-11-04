from ex import *
from ex.ioo import *
from ex.pp import *

import pyfits as pf
from scipy.signal import cspline1d, cspline1d_eval
import gc, pdb

def usage():
    print '''
fetch_make_fits.py working_dir stamp [nproc](1) [run](v_5_6_0)
'''
    sys.exit(0)

#resample spectra at single wavelength spectrum defined above
def TransformSpectrum(args):
    flux, invvar, c0, c1, newwave = args
    smoother = 3.0

    fitc = cspline1d(flux, lamb=smoother)
    fitc_iv = cspline1d(invvar, lamb=smoother)
    newf = cspline1d_eval(fitc, newwave, dx=c1, x0=c0)
    newiv   = cspline1d_eval(fitc_iv, newwave, dx=c1, x0=c0)

    return (newf, newiv)

def FindExistingPMs(working_dir):
    log.info('Finding what we have...')
    PMs = []
    fits = ExpandWildcard('%s/spectra_restframe_*.fits' % working_dir)
    for exfile in fits:
        hdus = pf.open(exfile, memmap=True)
        PMs.append(hdus[1].data['plate']*100000 + hdus[1].data['mjd'])
        hdus.close()
    if not PMs:
        return None
    else:
        return np.unique(np.hstack(PMs))

def FilterObjects(working_dir, spfile, 
                  zcut = (-1e3,1e-3), sncut = 30, 
                  wavelengthcut = (3856,9186), rfilter = 2):
    old_PMs = FindExistingPMs(working_dir)

    log.info('Finding what we want...')

    hdu = pf.open(spfile, memmap=True)
    spall = hdu[1].data

    # find only new ones
    if old_PMs is not None:
        now_PM = spall['PLATE']*100000 + spall['MJD']
        filt_pm = EncodeArray(now_PM, old_PMs, dtype = int32) < 0
        log.info('We already have %d Plate-MJD. We want %d new objects before filtering' % (len(old_PMs), filt_pm.sum()))
    else:
        filt_pm = np.ones(len(spall['Z']), dtype = 'bool')
        log.info('All new! We want %d objects before filtering' % (filt_pm.sum()))

    # filter by sky, z, s2n ratio, wavelength range
    filt_sky = spall['OBJTYPE'] != 'SKY'
    z = spall['Z']
    filt_z = (spall['Z'] >= zcut[0]) & (spall['Z'] <= zcut[1]) & (spall['ZWARNING'] == 0.)
    ssflux = spall['SPECTROSYNFLUX'][:,rfilter]
    ssflux_ivar = spall['SPECTROSYNFLUX_IVAR'][:,rfilter]
    s2n = ssflux*np.sqrt(ssflux_ivar)
    filt_s2n = s2n >= sncut
    wavemin, wavemax = spall['WAVEMIN'], spall['WAVEMAX']
    correctedmin, correctedmax = wavemin/(1. + z), wavemax/(1. + z)
    filt_wavelen = (correctedmin <= wavelengthcut[0]) & (correctedmax >= wavelengthcut[1])

    # select out indices of spall file that make all cuts
    filt_obj = reduce(np.logical_and, [filt_pm,filt_s2n,filt_sky,filt_z,filt_wavelen])

    log.info('%d / %d objects wanted' % (sum(filt_obj), len(filt_obj)))
    log.info('S2N=%d, SKY=%d, Z=%d, WL=%d' % (sum(filt_s2n & filt_pm), sum(filt_sky & filt_pm), sum(filt_z & filt_pm), sum(filt_wavelen & filt_pm)))

    result = spall[filt_obj].copy()
    hdu.close()

    return result

def ExtractPlate(now_p, spfiltered, rfilter, data_dir, run1d, run2d):
    flux,z,ra,dec,invvar,c0,c1,plate,mjd,fiber,sdssid,clas,subclas,s2n,eigenspectrum,magnitudes = [[] for i in range(16)]

    plate_idx = np.where(spfiltered['PLATE'] == now_p)[0]
    now_mjd = np.unique(spfiltered[plate_idx]['MJD'])
    
    file_prefix = '%s/plates/%d' % (data_dir, now_p)
    for m in np.arange(len(now_mjd)):
        now_m = now_mjd[m]

        try:
            plate_file = '%s/spPlate-%d-%d.fits' % (file_prefix, now_p, now_m)
            z_file     = '%s/%s/spZbest-%d-%d.fits' % (file_prefix, run1d, now_p, now_m)
            photo_file = '%s/photoPlate-%d-%d.fits' % (file_prefix, now_p, now_m)

            spallhdu = pf.open(plate_file)
            zanshdu  = pf.open(z_file)
            photohdu = pf.open(photo_file)
        except Exception as ex:
            log.info('! Error when processing {0}-{1}...\n{2}'.format(now_p, now_m, ex))
            continue

        zans         = zanshdu[1].data
        spall        = spallhdu[0].data
        spall1       = spallhdu[1].data
        spall5       = spallhdu[5].data
        phototable   = photohdu[1].data

        fiber_idx = plate_idx[spfiltered['MJD'][plate_idx] == now_m]
        fiber_ids = spfiltered[fiber_idx]['FIBERID']
        for fnd in np.arange(len(fiber_ids)):
            fid = fiber_ids[fnd] - 1

            flux.append(np.array(spall[fid,:]).copy())
            invvar.append(np.array(spall1[fid,:]).copy())
            c0.append(spallhdu[0].header['COEFF0'])
            c1.append(spallhdu[0].header['COEFF1'])
            z.append(zans[fid].field('z'))

            ra.append(spall5[fid].field('RA'))
            dec.append(spall5[fid].field('DEC'))
            tmp = spall5[fid].field('OBJID')
            sdssid.append('-'.join([str(oid) for oid in tmp]))
            tmp = fiber_idx[fnd]
            s2n.append(spfiltered['SPECTROSYNFLUX'][tmp,rfilter]*np.sqrt((spfiltered['SPECTROSYNFLUX_IVAR'][tmp,rfilter])))

            plate.append(now_p)
            mjd.append(now_m)
            fiber.append(fid + 1)
            clas.append(zans[fid].field('class'))
            subclas.append(zans[fid].field('subclass'))
            magnitudes.append(np.array(phototable['modelmag'][fid]).copy())

    return (flux,invvar,eigenspectrum,magnitudes,z,ra,dec,c0,c1,plate,mjd,fiber,sdssid,clas,subclas,s2n)

def main(working_dir, stamp, run, nproc):
    data_dir = '%s/data' % working_dir
    log.info('''
SDSS III Make FITS: 
Working dir: %s
Data dir   : %s
RUN        : %s
Stamp      : %s
''' % (working_dir, data_dir, run, stamp))

    # set top directory
    run2d, run1d = (run, run)
    spfilename   = 'spAll-' + run2d + '.fits'
    spfile       = data_dir + '/' + spfilename

    # find want we want to extract
    zcut = (-1e3, 0.36)
    sncut = 10
    rfilter = 2
    wavelengthcut = (3856,9186)
    spfiltered = FilterObjects(working_dir, spfile, zcut = zcut, sncut = sncut, wavelengthcut = wavelengthcut,rfilter = rfilter)
    if len(spfiltered) == 0: raise RuntimeError('no object to extract')

    gc.collect()

    ################### extract data

    log.info('Reading plate data')
    uniq_plates = np.unique(spfiltered['PLATE'])

    data = ExtractPlate(uniq_plates[0], spfiltered, rfilter, data_dir, run1d, run2d)
    for p in range(1, len(uniq_plates)):
        if p % 100 == 0: log.info('%d / %d' % (p + 1, len(uniq_plates)))
        dat = ExtractPlate(uniq_plates[p], spfiltered, rfilter, data_dir, run1d, run2d)
        for ind in range(len(data)): data[ind].extend(dat[ind])
    flux,invvar,eigenspectrum,magnitudes = data[:4]
    magnitudes = np.vstack(magnitudes)
    z,ra,dec,c0,c1,plate,mjd,fiber,sdssid,clas,subclas,s2n = [np.array(e) for e in data[4:]]
    del spfiltered, data

    ######### unredshift spectra

    nflux = len(flux)
    log.info('%d object actually extracted' % nflux)
    if nflux == 0: raise RuntimeError('no object actually extracted')

    #since all different lengths, determine largest, fill, then only select out nonzsero entries for fit
    length = np.array([np.shape(f)[0] for f in flux])
    dered_loglambda0 = c0 - np.log(1. + z)

    #define a single wavelength spectrum
    init_pixel   = np.log10(wavelengthcut[0])
    final_pixel  = np.log10(wavelengthcut[1])
    delta_pixel  = 1e-4 #10.**(np.min(dered_loglambda0))*(10.**1e-4 - 1.)
    new_wave     = np.arange(init_pixel, final_pixel, delta_pixel)

    log.info('Transforming spectra...')
    jobs = [(flux[i],invvar[i],dered_loglambda0[i],c1[i], new_wave)
            for i in range(nflux)]
    del flux, invvar
    gc.collect()

    results = ProcJobs(TransformSpectrum, jobs, nproc)
    newflux, newinvvar = zip(*results)
    newflux, newinvvar = np.vstack(newflux), np.vstack(newinvvar)

    log.info('Assembling FITS')

    col1 = pf.Column(name='z',           format='E',  array = z)
    col2 = pf.Column(name='ra',          format='E',  array = ra)
    col3 = pf.Column(name='dec',         format='E',  array = dec)
    col4 = pf.Column(name='plate',       format='I',  array = plate)
    col5 = pf.Column(name='mjd',         format='J',  array = mjd)
    col6 = pf.Column(name='fiber',       format='I',  array = fiber)
    col7 = pf.Column(name='class',       format='6A', array = clas)
    col8 = pf.Column(name='subclass',    format='6A', array = subclas)
    col9 = pf.Column(name='length',      format='I',  array = length)
    col10 = pf.Column(name='s2n',        format='E',  array = s2n)
    col11 = pf.Column(name='sdss_id',    format='20A',array = sdssid)

    cols = pf.ColDefs([col1, col2, col3, col4, col5, col6, 
                       col7, col8, col9, col10, col11])
    tablehdu = pf.new_table(cols)
    tablehdu.header.update('initp', init_pixel)
    tablehdu.header.update('finalp', final_pixel)
    tablehdu.header.update('stamp', np.int64(stamp.replace('-','')))
    imagehdu = pf.PrimaryHDU(newflux)

    hdulist = pf.HDUList([imagehdu, tablehdu])
    filename = '%s/spectra_restframe_%s.fits' % (working_dir, stamp)
    log.info('Saving FITS to %s' % filename)
    hdulist.writeto(filename, clobber=True)
    pf.append(filename, magnitudes)
    pf.append(filename, new_wave)
    pf.append(filename, newinvvar)

    log.info('Backing up FITS')
    os.system('cp %s %s/backup/' % (filename, working_dir))

if __name__ == '__main__':
    if len(sys.argv) < 3: usage()
    InitLog()

    working_dir = os.path.abspath(sys.argv[1])
    stamp = sys.argv[2]
    nproc = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
    run = sys.argv[4] if len(sys.argv) >= 5 else 'v5_6_0'

    main(working_dir, stamp, run, nproc)
