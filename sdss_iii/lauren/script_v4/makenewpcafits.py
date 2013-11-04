import numpy as np
import pyfits as pf
import scipy as sp
import gc
import os
import time
from scipy.signal import cspline1d, cspline1d_eval
import pdb
import esutil
import datetime

t0 = time.time()

#set top directory
#topdir     = '/astro/store/shared-scratch1/sdssspec/'
#topdir     = os.getenv('BOSS_SPECTRO_REDUX')
topdir = os.getcwd() + '/data'
#run2d      = 'v5_4_31/'
#run2d      = os.getenv('RUN2D')
run2d = 'v5_5_0'
#run1d      = '/v5_4_31/'
#run1d      = os.getenv('RUN1D')
run1d = run2d
#spfilename = 'spAll-v5_4_31.fits'
spfilename = 'spAll-' + run2d + '.fits'
spfile     = topdir + '/' + spfilename


#find wanted mjd/plate/fiber from spAll file
sncut   = 30.
rfilter = 2
zcut    = 0.001

combo    = []

logfile = open(topdir+'/logfile.txt', 'r')
for line in logfile:
	lastpartofline = line.split('/')[-1]
	if (len(lastpartofline.split('.')) > 1) & (len(lastpartofline.split('-')) > 2):
		if (lastpartofline.split('.')[-1] == 'fits\n') & (lastpartofline.split('-')[0] == 'spPlate'):
#			newmjd.append((lastpartofline.split('-')[2]).split('.')[0])
#			newplate.append(lastpartofline.split('-')[1])
			combo.append(lastpartofline.split('-')[1] + '-' + (lastpartofline.split('-')[2]).split('.')[0])
			print 'Read %s from logfile' % (lastpartofline.strip())
			
uniquecombo = np.unique(combo)
newmjd   = np.zeros(len(uniquecombo), dtype=int)
newplate = np.zeros(len(uniquecombo), dtype=int)
grabwantedobs = [] #np.zeros(len(uniquecombo), dtype=int)
print '%d unique combo found' % (len(uniquecombo))

#pdb.set_trace()

for i in range(len(uniquecombo)):
	newplate[i] = uniquecombo[i].split('-')[0]
	newmjd[i]   = uniquecombo[i].split('-')[1]

"""
read in logfile.txt
cut on '/' and then check that the first element cut on '-' is 'spPlate' and last element cut on '.' is 'fits'
   if true, grab plate, mjd and append to a list to check against spPlate for each fiber making cuts
"""

fitsFile = esutil.fits.FITS(spfile)
spall = fitsFile.read(1, columns = ['RA','DEC', 'OBJTYPE', 'Z', 'ZWARNING', 'SPECTROSYNFLUX', 'SPECTROSYNFLUX_IVAR', 'WAVEMIN', 'WAVEMAX', 'PLATE', 'MJD', 'FIBERID'])
###spallhdulist = pf.open(spfile, memmap=True)
###spall        = spallhdulist[1].data

for newobs in range(len(newplate)):
	grabwantedobs.append(np.where((spall['PLATE'] == newplate[newobs]) & (spall['MJD'] == newmjd[newobs]))[0].tolist())

listwantedobs = reduce(list.__add__, grabwantedobs, [])
listwantedobs.sort()

boolwantedobs = np.zeros(len(spall), dtype=bool)
boolwantedobs[:] = False
boolwantedobs[listwantedobs] = True

print 'read in'

"""
notsky  = spall.field('objtype') != 'SKY'
lowz    = (spall.field('z') <= zcut) & (spall.field('zwarning') == 0)
rs2n    = (spall.field('spectrosynflux')[:,rfilter])*np.sqrt((spall.field('spectrosynflux_ivar')[:,rfilter]))
"""

notsky = spall['OBJTYPE'] != 'SKY'
lowz    = (spall['Z'] <= zcut) & (spall['ZWARNING'] == 0.)
rs2n = (spall['SPECTROSYNFLUX'][:,rfilter])*np.sqrt((spall['SPECTROSYNFLUX_IVAR'][:,rfilter]))

goods2n = (rs2n >= sncut)


del rs2n

notsky     = np.array(notsky)
notskyinds = np.arange(0, len(spall))[notsky]

"""
wavemin = spall.field('wavemin')
wavemax = spall.field('wavemax')
z       = spall.field('z')
"""

wavemin = spall['WAVEMIN']
wavemax = spall['WAVEMAX']
z       = spall['Z']

correctedmin = wavemin/(1. + z)
correctedmax = wavemax/(1. + z)

del wavemin
del wavemax
del z

maxwavelength = 9186.
minwavelength = 3856.

goodwavelengths = np.bitwise_and(correctedmin <= minwavelength, correctedmax >= maxwavelength)
del correctedmin
del correctedmax

#logical step to select out indices of spall file that make all wanted cuts
spall2 = spall[np.bitwise_and(np.bitwise_and(np.bitwise_and(goods2n, np.bitwise_and(notsky, lowz)), goodwavelengths), boolwantedobs)].copy()
print '%d out of %d objects found after filtering' % (len(spall2), len(spall))
if len(spall2) == 0:
	print 'no worthy objects found. exiting.'
	exit(0)
###uniqplates = np.unique(spall2.field('plate'))
uniqplates = np.unique(spall2['PLATE'])
#spallhdulist.close()

del spall
del notsky
del lowz
del goods2n
del goodwavelengths
#del spallhdulist

gc.collect()

"""
Sometimes you want to have a list comprehension refer to itself, but you can't because it isn't bound to a name until after it is fully constructed. However, the interpreter creates a secret name that only exists while the list is being built. That name is (usually) '_[1]', and it refers to the bound method 'append' of the list. This is our back door to get at the list object itself.
5H"""

flux = []
z    = []
invvar = []
wave0 = []
wave1 = []
plate = []
mjd   = []
fiber = []
classification = []
subclass = []
#eigenspectrum = []
length = []
magnitudes = []
andmaskarray = []
ormaskarray = []
news2n    = []
#loop through all wanted indices of spall file and grab spectrum, invvar, etc. from the spplate files

for p in np.arange(len(uniqplates)):
	print p, '/', len(uniqplates)
###	nowplatestf   = spall2.field('plate') == uniqplates[p]
	nowplatestf   = spall2['PLATE'] == uniqplates[p]
	nowplatesindx = np.where(nowplatestf)
###	nowmjd        = np.unique(spall2[nowplatesindx].field('mjd'))
	nowmjd        = np.unique(spall2[nowplatesindx]['MJD'])
	spplatefilenameprefix = topdir + '/' + run2d + '/' 
	for m in np.arange(len(nowmjd)):        #len(nowplates)):
		with pf.open(spplatefilenameprefix+str(uniqplates[p])+'/spPlate-'+str(uniqplates[p])+'-'+str(nowmjd[m])+'.fits', memmap=True) as spallhdulist:
			try:
				zanshdulist  = pf.open(spplatefilenameprefix+str(uniqplates[p])+'/'+run1d+'/spZbest-'+str(uniqplates[p])+'-'+str(nowmjd[m])+'.fits', memmap=True)
				photohdulist = pf.open(spplatefilenameprefix+str(uniqplates[p])+'/photoPlate-'+       str(uniqplates[p])+'-'+str(nowmjd[m])+'.fits', memmap=True)
			except:
				print 'error when processing', uniqplates[p], '... skipping'
				continue
				
			zans         = zanshdulist[1].data
			spall        = spallhdulist[0].data
			spall1       = spallhdulist[1].data
			andmask      = spallhdulist[2].data
			ormask       = spallhdulist[3].data
			phototable   = photohdulist[1].data
			#wantedfiberindx  =  spall2[np.where(np.bitwise_and(spall2.field('plate')==uniqplates[p],spall2.field('mjd')==nowmjd))].field('fiberid')
			wantedfiberindx  =  spall2[np.where(np.bitwise_and(spall2['PLATE']==uniqplates[p],spall2['MJD']==nowmjd))]['FIBERID']
		                        
			for fib in np.arange(len(wantedfiberindx)):
				flux.append(np.array(spall[wantedfiberindx[fib]-1,:]).copy())
				invvar.append(np.array(spall1[wantedfiberindx[fib]-1,:]).copy())
				andmaskarray.append(np.array(andmask[wantedfiberindx[fib]-1,:]).copy())
				ormaskarray.append(np.array(ormask[wantedfiberindx[fib]-1,:]).copy())
#				eigenspectrum.append(np.array(zanshdulist[2].data[wantedfiberindx[fib]-1,:]).copy())
				wave0.append(spallhdulist[0].header['COEFF0'])
				wave1.append(spallhdulist[0].header['COEFF1'])
				z.append(zans[wantedfiberindx[fib]-1].field('z'))
				plate.append(uniqplates[p])
				mjd.append(nowmjd[m])
				fiber.append(wantedfiberindx[fib])
				classification.append(zans[wantedfiberindx[fib]-1].field('class'))
				subclass.append(zans[wantedfiberindx[fib]-1].field('subclass'))
				length.append(spallhdulist[0].header['NAXIS1'])
				magnitudes.append(np.array(phototable['modelmag'][wantedfiberindx[fib]-1]).copy())
			#print np.shape(wantedfiberindx)
			del zans
			del spall
			del spall1
			del phototable
			del wantedfiberindx
			zanshdulist._HDUList__file._File__file.close()
			spallhdulist._HDUList__file._File__file.close()
			zanshdulist.close()
			spallhdulist.close()
			photohdulist.close()
			  
			del zanshdulist
			del spallhdulist
			del photohdulist
	del nowplatestf
	del nowplatesindx
	del nowmjd
	gc.collect()

wave0 = np.array(wave0)
wave1 = np.array(wave1)
z     = np.array(z)
plate = np.array(plate)
mjd   = np.array(mjd)
fiber = np.array(fiber)
classification = np.array(classification)
length         = np.array(length)
magnitudes     = np.array(magnitudes)
andmaskarray   = np.array(andmaskarray)
ormaskarray    = np.array(ormaskarray)
invvar         = np.array(invvar)

#			if fib gt 0:

#unredshift spectra
maxwavelength = 9186
minwavelength = 3856.
fluxsize = len(flux)

deredloglambda0 = wave0 - np.log(1. + z)
length = np.zeros(len(flux))

#since all different lengths, determine largest, fill, then only select out nonzsero entries for fit
for m in np.arange(len(flux)):
    length[m] = np.shape(flux[m])[0]

wavevector = np.zeros((len(flux), np.max(length)+1))
for n in np.arange(len(flux)):
    wavevector[n,0:length[n]] = deredloglambda0[n]+(np.arange(length[n])*wave1[n])


#define a single wavelength spectrum
initialpixel = np.log10(minwavelength)
finalpixel   = np.log10(maxwavelength)
deltapix     = 1e-4 #10.**(np.min(deredloglambda0))*(10.**1e-4 - 1.)
npix         = (finalpixel - initialpixel)/deltapix + 1.
newwave      = initialpixel + deltapix*np.arange(npix)

newflux      = np.zeros((len(flux), npix+1))
newand       = np.zeros((len(flux), npix+1))
newor        = np.zeros((len(flux), npix+1))
chisq        = np.zeros(len(flux))
newinvvar    = np.zeros((len(flux), npix+1))


#resample spectra at single wavelength spectrum defined above
smoothing_parameter = 3.0
spline_order = 3
number_of_knots = -1

for p in range(len(flux)):
    nonzero = np.where(wavevector[p,:] != 0.)
    fitcoeff     = cspline1d(flux[p],   lamb=smoothing_parameter)
    fitcoeff_inv = cspline1d(invvar[p], lamb=smoothing_parameter)
    newflux[p,:]   = cspline1d_eval(fitcoeff,     newwave, dx=wave1[p], x0 = wavevector[p,0])
    newinvvar[p,:] = cspline1d_eval(fitcoeff_inv, newwave, dx=wave1[p], x0 = wavevector[p,0])
    oldfit = cspline1d_eval(fitcoeff, wavevector[p,nonzero][0], dx=wave1[p], x0 = wavevector[p,0])
    chisq[p] = np.sum(np.sqrt((oldfit - flux[p])**2.* [p]))/np.shape(flux[p])[0]
#    neweigen[p,0:length[p]] = eigenspectrum[p]

#pdb.set_trace()
t1 = time.time()
print t1-t0

#fitstable          = mytables.Table()
col1 = pf.Column(name='z',           format='E',  array = z)
col2 = pf.Column(name='plate',       format='I',  array = plate)
col3 = pf.Column(name='mjd',         format='L',  array = mjd)
col4 = pf.Column(name='fiber',       format='I',  array = fiber)
col5 = pf.Column(name='class',       format='6A', array = classification)
col6 = pf.Column(name='subclass',    format='6A', array = subclass)
col7 = pf.Column(name='length',      format='I',  array = length)

cols = pf.ColDefs([col1, col2, col3, col4, col5, col6, col7])
tablehdu = pf.new_table(cols)
imagehdu = pf.PrimaryHDU(newflux)

hdulist = pf.HDUList([imagehdu, tablehdu])

filename = 'pcaspectra_rest_new_{0}.fits'.format(datetime.datetime.now().strftime('%y%m%d-%H%M'))

hdulist.writeto(filename, clobber=True)

#pf.writeto(filename, newflux, clobber=True)
#pf.append(filename, newwave)
#pf.append(filename, z)
#pf.append(filename, plate)
#pf.append(filename, mjd)
#pf.append(filename, fiber)
#pf.append(filename, classification)
#mytables.write(fitstable, output=filename) 

#pf.append(filename, neweigen)
pf.append(filename, magnitudes)
pf.append(filename, newwave)
pf.append(filename, newinvvar)
#pf.append(filename, andmaskarray)
#pf.append(filename, ormaskarray)


