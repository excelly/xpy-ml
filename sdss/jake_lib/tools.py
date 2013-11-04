#!/astro/apps/pkg/python/bin/python

import numpy
import pylab
from matplotlib import ticker#, axes3d

import pyfits
import os


def S(theta):
    """
    returns x,y
      a 2-dimensional S-shaped function
      for theta ranging from 0 to 1
    """
    t = 3*numpy.pi * (theta-0.5)
    x = numpy.sin(t)
    y = numpy.sign(t)*(numpy.cos(t)-1)
    return x,y

def rand_on_S(N,sig=0,hole=False,outliers=0):
    t = numpy.random.random(N)
    x,z = S(t)
    y = numpy.random.random(N)*5.0
    if sig:
        x += numpy.random.normal(scale=sig,size=N)
        y += numpy.random.normal(scale=sig,size=N)
        z += numpy.random.normal(scale=sig,size=N)
    if outliers:
        x[:outliers] = -1.2+2.4*numpy.random.random(outliers)
        y[:outliers] = -0.2+5.4*numpy.random.random(outliers)
        z[:outliers] = -2.2+4.4*numpy.random.random(outliers)
        t[:outliers] = 0
    
    if hole:
        indices = numpy.where( ((0.3>t) | (0.7<t)) | ((1.0>y) | (4.0<y)) )
        #indices = numpy.where( (0.3>t) | ((1.0>y) | (4.0<y)) )
        return x[indices],y[indices],z[indices],t[indices]
    else:
        return x,y,z,t

def scatter_2D(x,y,t=None,cmap=pylab.cm.jet,clim=None,
               xlabel=None,ylabel=None,title=""):
    fig = pylab.figure()
    
    if t==None:
        cb = pylab.scatter(x,y,s=12.0,linewidths=0)
    else:
        cb = pylab.scatter(x,y,c=t,cmap=cmap,s=12.0,linewidths=0)

    if xlabel==None:
        xlabel = 'x'
    if ylabel==None:
        ylabel='y'
        
    pylab.xlabel(xlabel)
    pylab.ylabel(ylabel)
    pylab.title(title)

    pylab.colorbar(cb)

    if clim!=None:
        pylab.clim(clim[0],clim[1])

    return fig


def scatter_3D(x,y,z,t=None,cmap=pylab.cm.jet,clim=None,
               xlabel=None,ylabel=None,zlabel=None,title=None):
    fig = pylab.figure()
    ax = axes3d.Axes3D(fig)

    if t==None:
        cb = ax.scatter3D(x,y,z,s=12.0,linewidths=0)
    else:
        cb = ax.scatter3D(x,y,z,c=t,cmap=cmap,s=12.0,linewidths=0)

    #if x.min()>-2 and x.max()<2:
    #    ax.set_xlim(-2,2)
    
    if xlabel==None:
        xlabel = 'x'
    if ylabel==None:
        ylabel='y'
    if zlabel==None:
        zlabel='z'
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)

    ax.set_title(title)
    
    # elev, az
    ax.view_init(10, -80)

    cb = pylab.colorbar(cb)

    if clim!=None:
        cb.set_clim(clim[0],clim[1])

    return fig

def WriteMatrixFile(M,filename,description=""):
    D,N = M.shape

    of = open(filename,'w')

    of.write("N_POINTS:\t%i\n" % N)
    of.write("DIMENSION:\t%i\n" % D)
    of.write("DATA:\n")
    for s in description.split('\n'):
        of.write('# %s\n' % s)
    
    for j in range(N):
        for i in range(D):
            try:
                of.write("%g\t" % M[i,j])
            except:
                of.write("%s\t" % M[i,j])
                
        of.write("\n")

    of.close()

def WriteVectorFile(V,filename,description=""):
    N = len(V)

    of = open(filename,'w')

    of.write("N_POINTS:\t%i\n" % N)
    of.write("DATA:\n")
    for s in description.split('\n'):
        of.write('# %s\n' % s)
        
    for i in range(N):
        of.write("%g\n" % V[i])

    of.close()
            

def ReadMatrixFile(filename):
    F = open(filename,'r')

    nonfloats = []

    N = None
    D = None
    M = None

    for line in F:
        if line.strip().startswith("#"):
            continue
        elif line.startswith("N_POINTS:"):
            N = int(line.split()[1])
        elif line.startswith("DIMENSION:"):
            D = int(line.split()[1])
        elif line.startswith("DATA:"):
            if (N==None) or (D==None):
                raise ValueError, "Invalid file format: %s" % filename
            else:
                M = numpy.zeros([D,N])
                i=0
        elif (M is None):
            raise ValueError, "Invalid file format: %s" % filename
        else:
            line=line.split()
            for j in range(len(line)):
                try:
                    M[j,i] = float(line[j])
                except ValueError:
                    if str(j) not in nonfloats:
                        nonfloats.append(str(j))
                    M[j,i] = -888
            i+=1

    if len(nonfloats) != 0:
        print "%s: non-float values found in columns %s" %\
              (filename,', '.join(nonfloats))

    if i!=N:
        raise ValueError, "Not enough data points in %s" % filename

    return M
            

def ReadVectorFile(filename):
    F = open(filename,'r')

    N = None
    V = None

    for line in F:
        if line.startswith("#"):
            continue
        elif line.startswith("N_POINTS:"):
            N = int(line.split()[1])
        elif line.startswith("DIMENSION:"):
            print "ReadVectorFile: Warning: keyword DIMENSION found"
            print "   %s is a matrix file" % filename
        elif line.startswith("DATA:"):
            if (N==None):
                raise ValueError, "Invalid file format: %s" % filename
            else:
                V = numpy.zeros(N)
                i=0
        elif (V is None):
            raise ValueError, "Invalid file format: %s" % filename
        else:
            V[i] = float ( line.split()[0] )
            i+=1

    if i!=N:
        raise ValueError, "Not enough data points in %s" % filename

    return V

def getMatrixTags(filename):
    N = None
    for line in open(filename):
        if line.startswith('DIMENSION'):
            N = int(line.split()[1])
        if line.startswith('#') and N!=None:
            L = line.lstrip('#').split()
            if len(L) == N:
                return L
            else:
                return None
        if line.startswith('DATA'):
            return None
    return None

def getFITSMatrix(filename,tag=None):
    """
    from a fits file <filename> get the matrix in HDU specified by tag
    if tag is an integer or string representation of an integer,
      it is assumed to be the index of the HDU (starting from 1)
    if tag is a string, then routine checks for an HDU with
     header['EXTNAME'] == <tag>
    """
    hdulist = pyfits.open(filename)

    if tag in [None,""]:
        HDUnum = 0
    else:
        if type(tag) == type(1):
            HDUnum = tag-1
        elif type(tag) == type('abc'):
            if tag.isdigit():
                HDUnum = int(tag)-1
            else:
                HDUnum = -1
                for i in range(len(hdulist)):
                    try:
                        extname = hdulist[i].header['EXTNAME']
                    except:
                        continue
                    if extname.upper()==tag.upper():
                        HDUnum = i
                        break
                if HDUnum==-1:
                    raise ValueError, "%s not found in %s" % (tag,filename)
    
    return hdulist[HDUnum].data

def getFITSLambdas(filename):
    hdulist = pyfits.open(filename)

    coeff0 = hdulist[0].header['COEFF0']
    coeff1 = hdulist[0].header['COEFF1']
    N = hdulist[0].header['NAXIS1']

    return 10**(coeff0 + coeff1*numpy.arange(N))
    

def getFITSInfo(filename,infotag="",infohdu=1):
    hdulist = pyfits.open(filename)
    return hdulist[infohdu].data.field(infotag)

def create_fits(filename,spectra,**kwargs):
    """
    kwargs are in the form LABEL=DATATYPE
    """
    hdu = pyfits.PrimaryHDU()

    hdu.data = numpy.asarray(spectra)

    N = spectra.shape[0]

    Collist = []

    keys = kwargs.keys()
    keys.sort() #arrange keys alphabetically

    for key in keys:
        try:
            L = len(kwargs[key])
        except TypeError:
            L = 1

        if L==1:
            hdu.header.update(key.upper(),kwargs[key])
        elif L==N:
            format = numpy.asarray(kwargs[key]).dtype
            if format in ('int32','int64'):
                format = 'J'
            elif format in ('float32','float64'):
                format = 'E'
            elif str(format).startswith('|S'):
                format = 'A'+str(format)[2:]
            else:
                s = "unrecognized format: %s" % format
                raise ValueError, s
            Collist.append( pyfits.Column(name=key,
                                          format=format,
                                          array=kwargs[key]) )
        else:
            raise ValueError, "create_fits: key %s size does not match number of points"

    tbdhdu = pyfits.new_table(Collist)

    hdulist = pyfits.HDUList([hdu,tbdhdu])

    #clobber means overwrite existing file
    hdulist.writeto(filename,clobber=True)

def parse_FITS_filename(filename):
    """
    if filename is of the form '/path/to/myfile.fits+1'
     returns ('/path/to/myfile.fits','1')
    if filename is of the form '/path/to/myfile.fits[LABEL]'
     returns ('/path/to/myfile.fits','LABEL')
    aborts if filename cannot be parsed
    """
    filename.rstrip()

    L = len(filename)
    
    if filename[L-1] == ']':
        L = filename[:-1].split('[')
        if len(L)==1:
            raise ValueError, "%s cannot be parsed" % filename
        else:
            return '['.join(L[:-1]),L[-1]
            
        #i=L-2
        #while i>=0:
        #    if filename[i]=='[':
        #        return filename[:i],filename[i+1:L-1]
        #    i-=1
        #raise ValueError, "%s cannot be parsed" % filename

    if '+' in filename:
        L = filename.split('+')
        if L[-1].isdigit():
            return '+'.join(L[:-1]),L[-1]
        else:
            return filename,""

    return filename,""


def check_if_it_works():
    D = {}
    D['target'] = ['Target1','Target2']
    D['Z'] = [0.1,0.2]
    D['DZ'] = [0.005]
    
    for LINE in LINES:
        for info in ('flux','dflux','nsigma'):
            D[LINE+'_'+info] = [0.1,0.2]
            
    spectrum = [[1,2,3,4],[5,6,7,8]]

    D["COEFF0"] = 3.7
    D["COEFF1"] = 0.0001

    create_fits('tmp.fits',spectrum,**D)

    #check on the data
    hdulist = pyfits.open('tmp.fits')
    
    print hdulist[1].data.field('target')
    print hdulist[1].data.field('Z')
    print hdulist[1].data.field('DZ')
    hdulist.close()


if __name__ == '__main__':
    #filename = "/local/tmp/sdss_spec_2/1500.dat"
    #print filename
    #print parse_FITS_filename(filename)

    #exit()

    N=2000
    o=0

    if o:
        filename = 'test_data/S%io%i.fits' % (N,o)
    else:
        filename = 'test_data/S%i.fits' % (N)

    print filename
    
    x,y,z,t = rand_on_S(N,sig=0,hole=False,outliers=0)

    x[:o] = 2.4 * numpy.random.random(o)-1.2
    y[:o] = 5 * numpy.random.random(o)
    z[:o] = 4 * numpy.random.random(o)-2
    t[:o] = 0
    
    M = numpy.array([x,y,z]).T
    
    #WriteMatrixFile(M,'S%io%i.dat' % (N,o))
    #WriteMatrixFile(M1,'S%io%i-t.dat' % (N,o))

    create_fits(filename,M,**{'t':t,'coeff0':1})
            
            
        
                    
        
