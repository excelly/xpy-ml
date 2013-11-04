from ex import *
from datetime import datetime

from scipy.signal import cspline1d, cspline1d_eval
from scipy.special import hyp2f1 #hypergeometric function 2F1

O_M = 0.27            # omega matter
O_L = 0.73            # omega lambda
O_K = 1.0 - O_M - O_L # omega curvature
H_0 = 71.0            # Hubble constant (km/s/Mpc)
C   = 299792.458      # speed of light (km/s)
D_H = C/H_0           # Hubble distance (Mpc)
O_K_is_zero = (abs(O_K) < 1E-5) #close enough to zero

check(O_K_is_zero == True, 'omega curvature must be zero')

def PMF_N2S(pmf):
    return (str(int(pmf/1000000000)).zfill(4),
            str(int(pmf/10000) % 100000).zfill(5),
            str(int(pmf % 10000)).zfill(4))

def PMF_S2N(p, m, f):
    return int64(p)*1000000000 + int64(m)*10000 + int64(f)

def PMF_DashForm(p, m, f):
    result = '%s-%s-%s' % (str(p).zfill(4), str(m).zfill(5),
                           str(f).zfill(4))
    return result

def ComovingDistance(z):
    """
    line-of-sight comoving distance to a source at redshift z
    units will be the same as D_H, defined above.

    if O_K==0, this will compute the result analytically, using
    hypergeometric functions.

    if O_K!=0, this will compute the result using numerical integration
    of the function 1/H(z). this case is omitted here.
    """
    check(O_K_is_zero, 'the universe should be flat!')

    return D_H*2/sqrt(O_M)*(hyp2f1(1./6, 1./2, 7./6, -O_L/O_M) - hyp2f1(1./6, 1./2, 7./6, -O_L/O_M/(1+z)**3) / sqrt(1+z))

def RDZToCartesian(RA,Dec,Z):
    """
    RA and Dec are measured in degrees
    Z is redshift

    return value each row is (x,y,z)
    """
    
    theta = RA*pi/180.0 #azimuthal angle
    phi = Dec*pi/180.0  #polar angle
    r = ComovingDistance(Z) #comoving radius

    x = r*cos(theta)*cos(phi)
    y = r*sin(theta)*cos(phi)
    z = r*sin(phi)

    return hstack((col(x), col(y), col(z)))

def NameToRD(name):
    '''convert Jxxxxxx.x+xxxxxx.x name to (ra, dec)
    '''

    start = name.find('J') + 1
    mid = name.find('+', start)
    if mid < 0:
        mid = name.find('-', start)
    end = name.find(' ', mid)
    if end < 0:
        end = len(name)
			
    ra = name[start:mid]
    dec = name[mid:end]
    
    ra = (float(ra[0:2]) + float(ra[2:4])/60.0 + float(ra[4:])/3600.0)/24.0*360.0
    if dec.startswith('+'):
        dec = float(dec[1:3]) + float(dec[3:5])/60.0 + float(dec[5:])/3600.0
    else:
        dec = -(float(dec[1:3]) + float(dec[3:5])/60.0 + float(dec[5:])/3600.0)

    return (ra, dec)

def LookupRDZ(db, rdz, tol = 1e-2):
    '''look up in db the object with specified rdz

    return spec_id, ra, dec, z, matching error
    '''

    if len(rdz) == 3:
        ra, dec, z = rdz
        cmd = '''select specObjID, ra, dec, z from object_list where 
ra between {0} and {1} and 
dec between {2} and {3} and 
z between {4} and {5};'''.format(ra - tol, ra + tol, dec - tol, dec + tol, z - tol, z + tol)
        result = db.execute(cmd).fetchall()

        if len(result) == 0:
            return None
        else:
            spec_id, rr, dd, zz = unzip(result)
            dist = sos(hstack((col(rr)-ra, col(dd)-dec, (col(zz)-z))), 1)
    else:
        ra, dec = rdz
        cmd = '''select specObjID, ra, dec, z from object_list where 
ra between {0} and {1} and 
dec between {2} and {3};'''.format(ra - tol, ra + tol, dec - tol, dec + tol)
        result = db.execute(cmd).fetchall()

        if len(result) == 0:
            return None
        else:
            spec_id, rr, dd, zz = unzip(result)
            dist = sos(hstack((col(rr)-ra, col(dd)-dec)), 1)

    ii = argmin(dist)
    r = list(result[ii])
    r.append(sqrt(dist[ii]))
    r[0] = int64(r[0])
    return r

def LookupMPF(db, mjd, plate, fiber):
    '''look up mjd, plate, fiber
    return spec_id, ra, dec, z
    '''

    cmd = "select specObjID, ra, dec, z from object_list where mjd='{0}' and plate='{1}' and fiberID='{2}';".format(mjd, plate, fiber)
    result = db.execute(cmd).fetchall()
    if len(result) == 0:
        return None;
    else:
        return result[0]
    
def MaskFeature(feature, mask, bad_mask):
    '''set the badpixels in feature to nan
    '''

    check(mask.shape == feature.shape, 'shape not match')

    f = feature.copy()
    mask = (mask & bad_mask) > 0;

    for i in range(mask.shape[0]):
        f[i, mask[i]] = nan

    return f

def ComputeSpecCoeffs(wl_range, z_range, n_bin):
    c0 = log10(float(wl_range[0])/(1 + z_range[0]))
    c1 = (log10(float(wl_range[1])/(1 + z_range[1])) - c0)/n_bin
    return (c0, c1)

def RebinSpectra(spectra, c_old, c_new, nbin):
    '''rebin the spectra, one column per spectra
    the center wavelength at bin i is 10^(log10(1+z) + c0 + i*c1)
    '''

    dim_,n = spectra.shape
    c0_, c1_ = c_old
    c0, c1 = c_new

    result = zeros((dim, n), dtype = spectra.dtype)
    for i in range(dim):
        log_w_min_i = c0 + (i - 0.5)*c1
        log_w_max_i = log_w_min_i + c1
            
        binmin_i = int(floor((log_w_min_i - c0_)/c1_ + 0.5 ))
        binmax_i = int(ceil((log_w_max_i - c0_)/c1_ + 0.5 ))
        if binmin_i < 0: binmin_i = 0
        if binmax_i > dim_: binmax_i = dim_

        if binmin_i >=  binmax_i: 
            raise ValueError('Error in RebinSpectra')

        for j in range(binmin_i, binmax_i):
            log_w_min_j = c0_ + (j - 0.5)*c1_
            log_w_max_j = log_w_min_j + c1_

            result[i] += spectra[j]*(10**log_w_max_j - 10**log_w_min_j)
        # use the actual wl range. this is different from Rebin()
        lwmin = c0_ + (binmin_i - 0.5)*c1_
        lwmax = c0_ + (binmax_i - 0.5)*c1_
        result[i] /= (10**lwmax - 10**lwmin)

    # fig = figure()
    # ax1 = subplot(fig, 211)
    # ax2 = subplot(fig, 212)
    # for ind in range(min(3, spectra.size[1])):
    #     plot(spectra[:,ind], axes=ax1)
    #     plot(result[:,ind], axes=ax2)
    #     pause()

    return result

def SplineResample(y, n_x, x_range = None, smoother = 3):
    ''' Resample a signal y using spline.

    y: the signal must be sampled on uniform x
    n_x: number of points for the new signal
    x_range: tuple (start x, end x) of the signal
    smoother: spline smoothing strength
    '''

    if x_range is None: x_range = (0., 1.)
    spcoeffs = cspline1d(y, lamb = smoother)
    return cspline1d_eval(
        spcoeffs, linspace(x_range[0], x_range[1], n_x), 
        dx = (x_range[1]-x_range[0])/(len(y)-1.0), x0 = x_range[0])

def GetSkyImage(rd, scale=0.3, theta=None, size=200, opt=''):
    '''get the image of a object. theta is the radius of view range in
    degrees. theta will overrule scale
    '''

    if theta is not None: 
        scale = theta*2.*60*60/size
    scale = min(scale, 5)

    ra, dec = rd
    url='http://casjobs.sdss.org/ImgCutoutDR7/getjpeg.aspx?ra={0}&dec={1}&scale={2}&width={3}&height={3}&opt={4}'.format(ra, dec, scale, size, opt)
#    url='http://sdss.lib.uchicago.edu/ImgCutoutDR7/getjpeg.aspx?ra={0}&dec={1}&scale={2}&width={3}&height={3}&opt={4}'.format(rd[0], rd[1], scale, size, opt)
    return url

def GetStamp(now = None):
    if now is None: now = datetime.now()
    return now.strftime('%y%m%d-%H%M')

def MJD2CalDate(mjd):
    """Given mjd return calendar date. 
    returns YYMMDD
    """
    
    MJD0 = 2400000.5 # 1858 November 17, 00:00:00 hours 
    modf = np.modf
    mjd = arr(mjd)

    a = np.int32(mjd + MJD0 + 0.5)
    b = np.int32((a-1867216.25)/36524.25)
    c = a + b - np.int32(modf(b/4)[1]) + 1525 
    d = np.int32((c-122.1)/365.25)
    e = 365*d + np.int32(modf(d/4)[1])
    f = np.int32((c-e)/30.6001)

    day = c - e - np.int32(30.6001*f)
    month = f - 1 - 12*np.int32(modf(f/14)[1])
    year = d - 4715 - np.int32(modf((7+month)/10)[1])

    return (year % 100)*10000 + month*100 + day
