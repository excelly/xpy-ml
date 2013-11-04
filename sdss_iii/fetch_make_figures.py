from ex import *
from ex.pp import *

import pdb
import pyfits as pf
import matplotlib.pyplot as plt
print 'Pyplot backend:', plt.get_backend()
from matplotlib.font_manager import fontManager, FontProperties

import sdss.utils as utils
from sdss.settings import emission_lines

def usage():
    print '''
fetch_make_figures.py working_dir stamp [nproc](1) [run](v_5_6_0)
'''
    sys.exit(0)

font = FontProperties(size='x-small')
elines = sorted(emission_lines.items(), key=lambda l: l[0])
def GenerateFigure(args):
    plate, mjd, fibers, working_dir, run1d, run2d = args
    fileprefix = '%s/data/plates' % working_dir
    pm = '%d-%d' % (plate, mjd)
    log.debug('Processing: ' + pm)

    spplatefilename    = '%s/%d/spPlate-%s.fits' % (
        fileprefix, plate, pm)
    spzbestfilename    = '%s/%d/%s/spZbest-%s.fits' % (
        fileprefix, plate, run1d, pm)
    photoplatefilename = '%s/%d/photoPlate-%s.fits' % (
        fileprefix, plate, pm)

    spplatehdulist = pf.open(spplatefilename)
    zbesthdulist   = pf.open(spzbestfilename)
    photohdulist   = pf.open(photoplatefilename)

    zans     = zbesthdulist[1].data
    spplate  = spplatehdulist[0].data
    spplate1 = spplatehdulist[1].data

    plt.figure(1)
    for fiber in fibers:
        pmf = utils.PMF_DashForm(plate,mjd,fiber)
        out_dir = '%s/figures/%s' % (working_dir,str(plate).zfill(4))
        if not os.path.exists(out_dir): os.mkdir(out_dir)
        plotfilename = '%s/figure-%s.png' % (out_dir, pmf)
        if os.path.exists(plotfilename): continue
        
        # get scalar data
        c0 = spplatehdulist[0].header['COEFF0']
        c1 = spplatehdulist[0].header['COEFF1']
        length = spplatehdulist[0].header['NAXIS1']
        sky = spplatehdulist[6].data[fiber-1,:].copy()
        ra = spplatehdulist[5].data[fiber-1].field('RA')
        dec = spplatehdulist[5].data[fiber-1].field('DEC')
        z = zans[fiber-1].field('z')
        cla = zans[fiber-1].field('class')
        subcla = zans[fiber-1].field('subclass')
        
        # get curve data
        flux = spplate[fiber-1,:].copy()
        invvar = spplate1[fiber-1,:].copy()
        eigenspectrum  = zbesthdulist[2].data[fiber-1,:].copy()
        invvar[invvar < 1e-5] = 1e-5
        wavevector = np.power(10., c0 + np.arange(length)*c1)
        err = 1./np.sqrt(invvar)

        # plot curves
        plt.clf()
        plt.plot(wavevector, err, '-r')
        plt.plot(wavevector, sky, '-y')
        plt.plot(wavevector, eigenspectrum, '-b')
        plt.plot(wavevector, flux, '-k')
        
        fluxmin = np.min(flux)
        errmin  = np.min(err)
        ymin = np.min([fluxmin, errmin, 0])
        ymax = np.max(flux)
        yspan = ymax - ymin

        ystep = yspan*0.03
        ymin = -ystep*5
        ymax += yspan*0.1
        plt.ylim(ymin - ystep, ymax)
        
        # plot emission lines
        ypos = ymin
        for ii in range(len(elines)):
            lw, lname = elines[ii]
            if lw > wavevector[0] and lw < wavevector[-1]:
                plt.plot([lw, lw], [ymin, ymax], 'g:')
                plt.text(lw, ypos, lname, fontsize=8)
                ypos += ystep
                if ypos > -ystep: ypos = ymin

        # label the graph
        plt.title('Plate-MJD-Fiber: %s, %s(%s)\nZ=%0.4f, RA=%0.4f, DEC=%0.4f' % (pmf, cla, subcla, z, ra, dec))
        plt.legend(('Error', 'Sky', 'Best-Fit Eigen-Spectrum', 'Data'), loc=1, prop=font)
        plt.xlabel('Observed Wavelength [$\AA$]')
        plt.ylabel('Flux [$10^{-17}$ ergs/s/$\mathrm{cm^2}$/$\AA$]')

        # save the graph
        plt.savefig(plotfilename, facecolor='w', edgecolor='k')
        print 'Generated ' + plotfilename

    spplatehdulist.close()
    zbesthdulist.close()
    photohdulist.close()

def main(working_dir, stamp, run, nproc):
    log.info('''
SDSS III Make Figures: 
Working dir: %s
RUN        : %s
Stamp      : %s
''' % (working_dir, run, stamp))

    fits_filename = '%s/spectra_restframe_%s.fits' % (working_dir, stamp)
    log.info('Ploting figures for <%s> with %d processes' % (
            fits_filename, nproc))

    hdulist   = pf.open(fits_filename, memmap=True)
    platelist = hdulist[1].data.field('plate')
    mjdlist   = hdulist[1].data.field('mjd')
    fiberlist = hdulist[1].data.field('fiber')
    hdulist.close()

    log.info('%d figures to generate in %s/figures with %d processes' % (
            len(mjdlist),working_dir, nproc))
    MakeDir('figures')

    pms = list(set([str(platelist[i]).zfill(4) + str(mjdlist[i]).zfill(5)
                    for i in range(len(platelist))]))
    pms = [(int(pm[:4]), int(pm[4:])) for pm in pms]
    log.info('%d unique plate-mjd to process' % len(pms))

    jobs = [(p, m, fiberlist[(platelist == p) & (mjdlist == m)], working_dir, run, run) 
            for p, m in pms]
    ProcJobs(GenerateFigure, jobs, nproc)

if __name__ == '__main__':
    if len(sys.argv) < 3: usage()
    InitLog()

    working_dir = os.path.abspath(sys.argv[1])
    stamp = sys.argv[2]
    nproc = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
    run = sys.argv[4] if len(sys.argv) >= 5 else 'v5_6_0'

    main(working_dir, stamp, run, nproc)
