import numpy
from scipy import integrate
from scipy.special import hyp2f1 #hypergeometric function 2F1

"""
written by Jake VanderPlas, Feb 2010
 vanderplas@astro.washington.edu

Note: WMAP-5 parameters are (approximately)
 Omega matter = 0.27
 Omega lambda = 0.73
 Hubble Constant = 71.0
"""

O_M = 0.27            # omega matter
O_L = 0.73            # omega lambda
O_K = 1.0 - O_M - O_L # omega curvature
H_0 = 71.0            # Hubble constant (km/s/Mpc)
C   = 299792.458      # speed of light (km/s)
D_H = C/H_0           # Hubble distance (Mpc)

O_K_is_zero = (abs(O_K) < 1E-5) #close enough to zero

#integrand for comoving distance
H_inv = lambda z: 1/numpy.sqrt( O_M*(1.+z)**3 + O_K*(1.+z)**2 + O_L )

def comoving_distance(z):
    """
    line-of-sight comoving distance to a source at redshift z
    units will be the same as D_H, defined above.

    if O_K==0, this will compute the result analytically, using
    hypergeometric functions.

    if O_K!=0, this will compute the result using numerical integration
    of the function 1/H(z)
    """
    if O_K_is_zero:
        return D_H * 2. / numpy.sqrt(O_M) * \
               ( hyp2f1(1./6,1./2,7./6,-O_L/O_M) -\
                 hyp2f1(1./6,1./2,7./6,
                        -O_L/O_M/(1.+z)**3  )/numpy.sqrt(1.+z) )
    else:
        I,err = integrate.quad(H_inv,0,z)
        return D_H * I

def transverse_comoving_distance(z):
    """
    transverse comoving distance between two objects at redshift z.
    This is defined such that if the objects are separated by a small
    angle dtheta (in radians), the comoving distance between them
    is transverse_comoving_distance(z) * dtheta

    Note that for O_K==0, this is trivial.  For O_K!=0, space is
    non-Euclidean and this is less trivial.
    """
    D_C = comoving_distance(z)
    if O_K_is_zero:
        return D_C
    elif O_K > 0:
        sOK = numpy.sqrt(O_K)
        return D_H/sOK * numppy.sinh(sOK*D_C/D_H)
    elif O_K < 0:
        sOK = numpy.sqrt(-O_K)
        return D_H/sOK * numppy.sin(sOK*D_C/D_H)

def convert_to_cartesian(RA,Dec,Z):
    """
    RA and Dec are measured in degrees
    Z is redshift

    return value is a tuple (x,y,z)
    of cartesian coordinates, with Earth at the origin
    """
    if not O_K_is_zero:
        raise ValueError, \
              "cartesian coordinates are not applicable to nonzero curvature"
    
    theta = RA*numpy.pi/180. #azimuthal angle
    phi = Dec*numpy.pi/180.  #polar angle
    r = comoving_distance(Z) #comoving radius

    x = r*numpy.cos(theta)*numpy.sin(phi)
    y = r*numpy.sin(theta)*numpy.sin(phi)
    z = r*numpy.cos(phi)

    return (x,y,z)

if __name__ == '__main__':
    import pylab
    z = numpy.linspace(0,5,1000)
    D = comoving_distance(z)
    pylab.plot(z,D)
    pylab.xlabel('redshift')
    pylab.ylabel('line-of-sight comoving distance (Mpc)')
    pylab.show()
