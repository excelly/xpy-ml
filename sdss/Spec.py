# SF: scalar feature
# VF: vector feature
# LF: line feature

from ex import *
from ex.ioo.FITS import FITS
from ex.plott import *

import settings

# default scalar fields to extract from the FITS files
default_sf_names = ['Z','Z_ERR','COEFF0','COEFF1', 'SPEC_CLN', 'MAG_G','MAG_R','MAG_I', 'Z_STATUS', 'Z_WARNIN', 'RAOBJ', 'DECOBJ', 'SN_I', 'SN_R', 'SN_G', 'NGOOD']

# default lines to extract from the FITS files
default_lines = [line[0] for line in settings.emission_lines.items() if line[0] > 3830]

class Spec:

    def __init__(self, fits_file, sf_names, lines):
        fits = FITS(fits_file)
        hdulist = fits.HDUs

        try: 
            hdulist[0].verify('fix')
        except: 
            raise RuntimeError("failed to verify FITS file %s"
                               % fits_file)

        # vector features
        self.VFNames = ['spectrum','continuum','noise','mask']
        self.VF = {}
        for i in range(len(self.VFNames)):
            self.VF[self.VFNames[i]] = hdulist[0].data[i, :]
        self.VF['continuum'] = self.VF['spectrum'] - self.VF['continuum']

        # scalar features
        self.SFNames = sf_names
        self.SF = {}
        pri_header = hdulist[0].header
        for key in self.SFNames:
            self.SF[key] = pri_header[key]
        
        self.MPF = "{0}-{1}-{2}".format(
            pri_header['MJD'], 
            str(pri_header['PLATEID']).zfill(4), 
            str(pri_header['FIBERID']).zfill(3))

        self.Coeff = [self.SF['COEFF0'], self.SF['COEFF1']]

        # line feature
        self.LF = None
        if hdulist[2].data is not None:
            self.LF = {}
            ld = hdulist[2].data
            lines = dict(zip(['%0.1f' % line for line in lines], [1]*len(lines)))
            for i in range(ld.shape[0]):
                line = '%.1f' % hdulist[2].data.field('restWave')[i]
                if line in lines:
                    wave = ld.field('wave')[i]
                    sig = ld.field('sigma')[i]
                    dsig = ld.field('sigmaErr')[i]
                    height = ld.field('height')[i]
                    dheight = ld.field('heightErr')[i]
                    ew = ld.field('ew')[i]
                    nsigma = ld.field('nsigma')[i]
                    cont = ld.field('continuum')[i]
                    chisq = ld.field('chisq')[i]

                    # (center, flux, dflux, width, dwidth, nsigma)
                    # self.LF[line] = arr((wave, sig*height, sig*dheight+dsig*height, sig, dsig, nsigma))
                    self.LF[line] = arr((height, dheight, sig, dsig, ew, nsigma, cont))
                    lines[line] = -1

            for key, val in lines.items():
                if val > 0:
                    log.warn('incomplete line features at {0}'.format(key))
                    self.LF = None
            
        self.in_rest_frame = False

    def __len__(self):
        return len(self.VF['spectrum'])

    def SetCoeff(self, coeff):
        self.Coeff = coeff
        self.SF['COEFF0'] = coeff[0]
        self.SF['COEFF1'] = coeff[1]

    def ChangeFrame(self, to_rest = True):
        c0, c1 = self.Coeff
        if to_rest and not self.in_rest_frame:
            self.SetCoeff([c0 - log10(1 + self.SF['Z']), c1])
            self.in_rest_frame = True
        elif not to_rest and self.in_rest_frame:
            self.SetCoeff([c0 + log10(1 + self.SF['Z']), c1])
            self.in_rest_frame = False

    def __str__(self):
        return "SDSS Spec {0}: Z = {1}, Coeff = {2}".format(
            self.MPF, self.SF['Z'], self.Coeff)

    def LogWRange(self, i = None):
        '''get the range of wave length corresponding to each bin
        '''

        c0, c1 = self.Coeff

        if i is None:
            return (c0 + (0 - 0.5)*c1, 
                    c0 + (len(self) + 0.5)*c1)
        else:
            return (c0 + (i - 0.5)*c1,
                    c0 + (i + 0.5)*c1)

    def WRange(self, i = None):
        wmi, wma = self.LogWRange(i)
        return (10**wmi, 10**wma)
        
    def WaveLength(self):
        c0, c1 = self.Coeff
        return 10** (c0 + c1*arange(len(self)))

    def BinRange(self, w_min, w_max, offset = 0):
        return self.BinRangeLog(log10(w_min), log10(w_max), offset)

    def BinRangeLog(self, log_w_min, log_w_max, offset = 0):
        c0, c1 = self.Coeff

        imin = int( floor( (log_w_min - c0)/c1 + offset ) )
        imax = int( ceil( (log_w_max - c0)/c1 + offset ) )

        return (imin, imax)

    def RemoveSkyLines(self):
        """
        removes strong Oxygen line at 5577A, 6300A, and 6365A from each
        row of spectrum. This basically does a linear interpolation across
        those regions
        """

        spectrum = self.VF['spectrum']

        for line in (5577,6300,6365):
            imin, imax = self.BinRange(line - 10, line + 10)

            if imin < 0 or imax >= len(self):
                log.warn("warning: line {0} out of range".format(line))

            s0 = spectrum[imin]
            ds_di = (spectrum[imax] - s0)/(imax - imin)

            ind = arange(1, imax - imin, dtype = spectrum.dtype)
            spectrum[int32(ind + imin)] = s0 + ds_di*ind

    def ReBin(self, c0, c1, dim):
        '''rebin the spectrum
        the center wavelength at bin i is 10^(log10(1+z) + c0 + i*c1)
        '''

        new_spec = pycopy.deepcopy(self)
        new_spec.SetCoeff([c0, c1])
        
        c0_spec, c1_spec = self.Coeff

        spectrum_spec = self.VF['spectrum']
        continuum_spec = self.VF['continuum']
        noise_spec = self.VF['noise']
        mask_spec = int32(self.VF['mask'])

        spectrum = zeros(dim, dtype = spectrum_spec.dtype)
        continuum = zeros(dim, dtype = continuum_spec.dtype)
        noise = zeros(dim, dtype = noise_spec.dtype)
        mask = zeros(dim, dtype = mask_spec.dtype)

        or_op = lambda x,y: x | y
        for i in range(dim):
            log_w_min_i = c0 + (i - 0.5)*c1
            log_w_max_i = log_w_min_i + c1

            binmin_i, binmax_i = self.BinRangeLog(log_w_min_i, log_w_max_i, 0.5)

            binmin_i = max(0, binmin_i)
            binmax_i = min(len(self), binmax_i)
            if binmin_i >=  binmax_i:
                raise ValueError('bad c0, c1, or nbins\n{0}\n{1}'.format(self, new_spec))

            r = 0
            rc = 0
            for j in range(binmin_i, binmax_i):
                log_w_min_j = c0_spec + (j - 0.5)*c1_spec
                log_w_max_j = log_w_min_j + c1_spec

                if log_w_min_j < log_w_min_i: 
                    log_w_min_j = log_w_min_i
                if log_w_max_j > log_w_max_i: 
                    log_w_max_j = log_w_max_i

                tt = 10**log_w_max_j - 10**log_w_min_j
                r += spectrum_spec[j]*tt
                rc += continuum_spec[j]*tt

            tt = 10**log_w_max_i - 10**log_w_min_i
            spectrum[i] = r/tt
            continuum[i] = rc/tt
            noise[i] = sqrt(sum(noise_spec[binmin_i:binmax_i]**2))
            mask[i] = reduce(or_op, mask_spec[binmin_i:binmax_i])

        new_spec.VF['spectrum'] = spectrum
        new_spec.VF['continuum'] = continuum
        new_spec.VF['noise'] = noise
        new_spec.VF['mask'] = mask

        return new_spec

    def Integrate(self, w_min = None, w_max = None, feature = 'spectrum'):
        """
        note that wmin and wmax are in linear angstroms,
        not log angstroms!
        """

        lwr = self.LogWRange()

        log_w_min = lwr[0] if w_min is None else log10(w_min)
        log_w_max = lwr[1] if w_max is None else log10(w_max)            

        if log_w_min < lwr[0] or log_w_max > lwr[1]:
            raise ValueError('w out of range')
        
        i_min, i_max = self.BinRangeLog(log_w_min, log_w_max)
        i_min = max(i_min, 0)
        i_max = min(i_max, len(self))

        spectrum = self.VF[feature]
        tot_flux = 0
        for i in range(i_min,i_max):
            log_w_min_i, log_w_max_i = self.LogWRange(i)
            log_w_min_i = max(log_w_min, log_w_min_i )
            log_w_max_i = min(log_w_max, log_w_max_i )

            tot_flux += spectrum[i] * (10**log_w_max_i - 10**log_w_min_i)
        return tot_flux

    def Normalize(self,N = 1, feature = 'spectrum'):
        '''normalize the total flux
        '''

        I = self.Integrate(feature = feature)
        if I <= 0:
            raise ValueError("error: cannot normalize. I = 0")
        self.VF[feature] /= N*I

    def Plot(self):
        wl = self.WaveLength()
        plot(wl, self.VF['spectrum'], 'r', wl, self.VF['continuum'], 'b')

    @staticmethod
    def Assemble(spec_list, lines = None):
        '''assemble a list of specs in to matrices and arrays
        '''

        n = len(spec_list)
        dim = len(spec_list[0])

        # vector features
        vfnames = spec_list[0].VF.keys()
        vf_list = [spec.VF for spec in spec_list]
        vf = {}
        for vn in vfnames:
            vf[vn] = AssembleMatrix(vf_list, vn)

        # scalar features
        sf_list = [spec.SF for spec in spec_list]
        sf_names = spec_list[0].SF.keys()
        sf = {}
        for sn in sf_names:
            sf[sn] = AssembleVector(sf_list, sn)

        # line features
        if lines is not None:
            lf_list = [spec.LF for spec in spec_list]
            lf = {}
            for line in lines:
                line_str = '%.1f' % line
                lf[line_str] = AssembleMatrix(lf_list, line_str)
        else:
            lf = None

        # other info
        mpfs = [spec.MPF for spec in spec_list]

        return {'MPF': mpfs, 'SF': sf, 'VF': vf, 'LF': lf}
        
if __name__ == '__main__':

    fits_file = sys.argv[1]

    from sdss.jake_lib.SDSSfits import SDSSfits
    spec = Spec(fits_file, default_sf_names, default_lines)
    specex = SDSSfits(fits_file)

    rebin_length = 1000
    factor = (len(specex) - 1.0)/rebin_length
    rebin_coeff1 = factor * specex.coeff1
    rebin_coeff0 = specex.coeff0 + 0.5*factor*specex.coeff1

    spec = spec.ReBin(rebin_coeff0,rebin_coeff1,rebin_length)
    specex = specex.rebin(rebin_coeff0,rebin_coeff1,rebin_length)

    figure()
    spec.Plot()
    specex.plot('g')
    draw()
    pause()

    spec.RemoveSkyLines()
    specex.remove_O_lines()

    cla()
    spec.Plot()
    specex.plot('g')
    draw()
    pause()
