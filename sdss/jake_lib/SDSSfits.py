#!/astro/apps/pkg/python/bin/python

import numpy
import pyfits
import pylab
import os

class SDSSfits:
    def __init__(self,SDSS_fitfile = None,LINES=[]):
        self.spectrum = None

        self.D = {}

        self.z = 0
        self.coeff0 = 0
        self.coeff1 = 0
        self.name = ""
        
        if SDSS_fitfile != None:
            hdulist = pyfits.open(SDSS_fitfile)

            self.spectrum = hdulist[0].data[0]
            self.name = hdulist[0].header['NAME']

            self.D['N_BAD_PIX'] = sum(hdulist[0].data[2]==0)

            for key in ('Z','Z_ERR','COEFF0','COEFF1',
                        'SPEC_CLN','MAG_G','MAG_R','MAG_I'):
                self.D[key] = hdulist[0].header[key]

            self.D['TARGET'] = SDSS_fitfile

            #get line data
            hdu_line_list = dict([(line,-1) for line in LINES])
            if hdulist[2].data == None:
                self.numlines = 0
            else:
                self.numlines = hdulist[2].data.shape[0]
                for i in range(self.numlines):
                    line_w = hdulist[2].data.field('restWave')[i]
                    line_str = '%.2f' % line_w
                    if line_str in LINES:
                        hdu_line_list[line_str] = i
                    
                for line in LINES:
                    i = hdu_line_list[line]
                    #compute flux and dflux, get nsigma

                    if i<0:
                        sig = 0
                        dsig = 0
                        height = 0
                        dheight = 0
                        nsigma = 0
                    else:
                        sig = hdulist[2].data.field('sigma')[i]
                        dsig = hdulist[2].data.field('sigmaErr')[i]
                        height = hdulist[2].data.field('height')[i]
                        dheight = hdulist[2].data.field('heightErr')[i]
                        nsigma = hdulist[2].data.field('nsigma')[i]

                    if sig==-9999: sig=0
                    if height==-9999: height=0
                    if nsigma==-9999: nsigma=0
                
                    self.D[line+'_flux'] = sig*height
                    self.D[line+'_dflux'] = sig*dheight + dsig*height
                    self.D[line+'_width'] = sig
                    self.D[line+'_dwidth'] = dsig
                    self.D[line+'_nsigma'] = nsigma

            self.z = self.D['Z']
            self.coeff0 = self.D['COEFF0']
            self.coeff1 = self.D['COEFF1']
            
            hdulist.close()
            
    def plot(self,*args,**kwargs):
        pylab.plot(self.wavelength(),self.spectrum,*args,**kwargs)

    def log_w_min(self,i=None):
        """
        if i is specified, return log_w_min of bin i
        otherwise, return log_w_min of the spectrum
        """
        if i==None: i=0
        return self.coeff0 + (i-0.5)*self.coeff1

    def log_w_max(self,i=None):
        """
        if i is specified, return log_w_max of bin i
        otherwise, return log_max of the spectrum
        """
        if i==None: i=len(self)-1
        return self.coeff0 + (i+0.5)*self.coeff1

    def w_min(self,i=None):
        return 10**self.log_w_min(i)

    def w_max(self,i=None):
        return 10**self.log_w_max(i)
        
    def wavelength(self):
        return 10** (self.coeff0+self.coeff1*numpy.arange(len(self)))

    def __len__(self):
        return len(self.spectrum)

    def remove_O_lines(self):
        """
        removes strong Oxygen line at 5577A, 6300A, and 6365A.
        This basically does a linear interpolation across those
        regions
        """
        for line in (5577,6300,6365):
            lmin = line-10
            lmax = line+10
            
            imin = int( numpy.floor( (numpy.log10(lmin)-self.coeff0)/self.coeff1 ) )
            imax = int( numpy.ceil( (numpy.log10(lmax)-self.coeff0)/self.coeff1 ) )

            if imin<0 or imax>=len(self.spectrum):
                print "warning: line %i out of range\n" % line

            s0 = self.spectrum[imin]
            ds_di = (self.spectrum[imax] - self.spectrum[imin])/(imax-imin)

            for i in range(imin+1,imax):
                self.spectrum[i] = s0 + (i-imin)*ds_di

    def move_to_restframe(self):
        if (self.z < 0):
            print "warning: negative redshift!  Can't move to rest frame"
        self.coeff0 -= numpy.log10(1+self.z)
        self.z = 0.0

    def rebin(self,rebin_coeff0,rebin_coeff1,rebin_length):
        snew = self.__class__()
        snew.spectrum = numpy.zeros(rebin_length)
        snew.z = self.z
        snew.coeff0 = rebin_coeff0
        snew.coeff1 = rebin_coeff1

        snew.D = self.D.copy()
    
        if ( self.log_w_min() > snew.log_w_min()+1E-10 ):
            raise ValueError,"rebin: new_min preceeds old_min"
        
        if ( self.log_w_max() < snew.log_w_max()-1E-10 ):
            raise ValueError,"rebin: new_max exceeds old_max"
        
        for i in range(len(snew)):
            log_wi_new = snew.coeff0 + i*snew.coeff1
            log_w_min_i = snew.log_w_min(i)
            log_w_max_i = snew.log_w_max(i)

            #integrate old flux within this range
            binmin_j = numpy.floor((log_w_min_i - self.coeff0)/self.coeff1+ 0.5)
            binmax_j = numpy.ceil ((log_w_max_i - self.coeff0)/self.coeff1+ 0.5)

            if binmin_j == -1:
                binmin_j = 0
            elif binmin_j < -1:
                raise ValueError, "error: binmin_j too small"
            
            if binmax_j == len(self)+1:
                binmax_j = len(self)
            elif binmax_j > len(self)+1:
                raise ValueError, "error: binmax_j too large"

            snew.spectrum[i]=0

            for j in range( int(binmin_j), int(binmax_j) ):
                log_w_min_j = max(log_w_min_i, self.log_w_min(j) )
                log_w_max_j = min(log_w_max_i, self.log_w_max(j) )

                snew.spectrum[i] += self.spectrum[j] * \
                                    (10**(log_w_max_j) - 10**(log_w_min_j))

            snew.spectrum[i] /= (10**(log_w_max_i) - 10**(log_w_min_i))
        
        return snew

    def integrate(self,w_min = None, w_max = None):
        """
        note that wmin and wmax are in linear angstroms,
        not log angstroms!
        """
        if w_min == None:
            log_w_min = self.log_w_min()
        else:
            log_w_min = numpy.log10(w_min)
            
        if w_max == None:
            log_w_max = self.log_w_max()
        else:
            log_w_max = numpy.log10(w_max)

        

        if (log_w_min < self.log_w_min()-1E-10) or\
               (log_w_max > self.log_w_max()+1E-10):
            print "Error: integrate(): integration bounds exceed spectrum range"
            print "Abort"
            exit(-1)
            
        
        i_min = numpy.floor((log_w_min - self.coeff0)/self.coeff1+ 0.5)
        i_max = numpy.ceil ((log_w_max - self.coeff0)/self.coeff1+ 0.5)

        if(i_min == -1):
            i_min += 1

        if(i_max == len(self)+1):
            i_max -= 1
        
        tot_flux = 0
        for i in range(int(i_min),int(i_max)):
            log_w_min_i = max(log_w_min, self.log_w_min(i) )
            log_w_max_i = min(log_w_max, self.log_w_max(i) )

            tot_flux += self.spectrum[i] * (10**log_w_max_i - 10**log_w_min_i)
        return tot_flux

    def normalize(self,N=1):
        I = self.integrate()
        if self.integrate()<=0:
            raise ValueError, "error: cannot normalize. I=0"
        
        self.spectrum /= self.integrate()
        self.spectrum *= N
            
        
    
if __name__ == '__main__':

    FIT_FILE = 'spSpec-51630-0266-104.fit'
    
    spec = SDSSfits(FIT_FILE)
    print spec.w_min(), spec.w_max()
    
    spec.plot(c='#AAAAAA')

    #spec.remove_O_lines()
    
    #spec.move_to_restframe()
    
    rebin_length = 1000
    factor = (len(spec) - 1.0)/rebin_length
    rebin_coeff1 = factor * spec.coeff1
    rebin_coeff0 = spec.coeff0 + 0.5*factor*spec.coeff1
    spec_rebin = spec.rebin(rebin_coeff0,rebin_coeff1,rebin_length)
    spec_rebin.plot(c='b')
    
    pylab.show()
