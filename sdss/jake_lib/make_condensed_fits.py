#!/astro/apps/pkg/python/bin/python

import pyfits
import SDSSfits
import numpy
from tools import create_fits
import os
    

def main(OUT_DIR = "/astro/net/scratch1/vanderplas/SDSS_GAL_RESTFRAME/",
         DIR_ROOT = "/astro/net/scratch1/sdssspec/spectro/1d_26/*/1d",
         LINES_FILE = "LINES_SHORT.TXT",
         z_min = 0.0,   #zmax is set such that SII lines will 
         z_max = 0.36,  # fall in range of 3830 to 9200 angstroms
         rebin_coeff0 = 3.583,     # rebin parameters give a wavelength
         rebin_coeff1 = 0.0002464, # range from 3830A to 9200A
         rebin_length = 1000,
         remove_sky_absorption = True,
         normalize = True):    

    LINES = []
    KEYS = ['TARGET','Z','Z_ERR','SPEC_CLN','MAG_G','MAG_R','MAG_I','N_BAD_PIX']

    if LINES_FILE is not None:
        for line in open(LINES_FILE):
            line = line.split()
            if len(line)==0:continue
            W = float(line[0])
            if W<3000 or W>7000:continue
            LINES.append('%.2f'%W)
            for info in ('flux','dflux','width','dwidth','nsigma'):
                KEYS.append('%.2f_%s' % (W,info) )


    for SET in os.listdir(DIR_ROOT.split('*')[0]):
        if not SET.isdigit():
            continue
        DIR = DIR_ROOT.replace('*',SET)
        if not os.path.exists(DIR):
            continue
        
        OUT_FILE = os.path.join(OUT_DIR,SET+'.dat')

        print 'writing %s' % os.path.join(OUT_DIR,SET+'.dat')

        col_dict = dict([(KEY,[]) for KEY in KEYS])
        spec_list = []

        NUMS = []

        for F in os.listdir(DIR):
            if not F.endswith('.fit'): continue

            num = int( F.strip('.fit').split('-')[-1] )
            if num in NUMS:
                #print " - already measured: skipping %s" % F
                continue

            #open hdu file and glean necessary info
            SPEC = SDSSfits.SDSSfits(os.path.join(DIR,F),LINES)

            if SPEC.D['SPEC_CLN'] not in (1,2,3,4):
                continue

            if SPEC.z<z_min:
                #print " - negative z: skipping %s" % F
                continue
            if SPEC.z>z_max:
                #print " - z>z_max: skipping %s" % F
                continue
            if SPEC.numlines == 0:
                #print " - no line measurements: skipping %s" % F
                continue

            if remove_sky_absorption:
                #cover up strong oxygen absorption
                SPEC.remove_O_lines()

            #move to restframe, rebin, and normalize
            SPEC.move_to_restframe()
            try:
                SPEC = SPEC.rebin(rebin_coeff0,rebin_coeff1,rebin_length)
            except:
                print "  rebin failed.  Skipping %s" % F
                continue

            if normalize:
                try:
                    SPEC.normalize()
                except:
                    print "  normalize failed.  Skipping %s" % F
                    continue

            if min(SPEC.spectrum) < -4*max(SPEC.spectrum):
                print "  goes too far negative.  Skipping %s" % F
            
            NUMS.append(num)

            spec_list.append(SPEC.spectrum.tolist())

            for KEY in KEYS:
                col_dict[KEY].append(SPEC.D[KEY])

            del SPEC

        if os.path.exists(OUT_FILE):
            os.system('rm %s' % OUT_FILE)

        col_dict['coeff0'] = rebin_coeff0
        col_dict['coeff1'] = rebin_coeff1
        
        create_fits(OUT_FILE,numpy.asarray( spec_list ),**col_dict)

        print " - wrote %i spectra" % len(NUMS)
            

if __name__ == '__main__':
    main(OUT_DIR = "/astro/net/scratch1/vanderplas/SDSS_GAL_RESTFRAME/",
         DIR_ROOT = "/astro/net/scratch1/sdssspec/spectro/1d_26/*/1d",
         #LINES_FILE = "LINES_SHORT.TXT",
         LINES_FILE = None,
         z_min = 0.0,   #zmax is set such that SII lines will 
         z_max = 0.36,  # fall in range of 3830 to 9200 angstroms
         rebin_coeff0 = 3.583,     # rebin parameters give a wavelength
         rebin_coeff1 = 0.0002464, # range from 3830A to 9200A
         rebin_length = 1000,
         remove_sky_absorption = False,
         normalize = False)
