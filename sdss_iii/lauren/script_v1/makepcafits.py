#! /bin/usr python 

import matplotlib 
import numpy as np
import pyfits as pf
import scipy as sp
import gc
import os
import time
from scipy.signal import cspline1d, cspline1d_eval
import pdb

t0 = time.time()

#set top directory
#topdir     = '/astro/store/shared-scratch1/sdssspec/'
topdir     = os.getenv('BOSS_SPECTRO_REDUX')
#run2d      = 'v5_4_31/'
run2d      = os.getenv('RUN2D')
#run1d      = '/v5_4_31/'
run1d      = os.getenv('RUN1D')
#spfilename = 'spAll-v5_4_31.fits'
spfilename = 'spAll-' + run2d + '.fits'
spfile     = topdir + '/' + spfilename


#find wanted mjd/plate/fiber from spAll file
sncut   = 30.
rfilter = 2
zcut    = 0.001
	
spallhdulist = pf.open(spfile, memmap=True)
spall        = spallhdulist[1].data

print 'read in'

notsky  = spall.field('objtype') != 'SKY'
lowz    = (spall.field('z') <= zcut) & (spall.field('zwarning') == 0)
rs2n    = (spall.field('spectrosynflux')[:,rfilter])*np.sqrt((spall.field('spectrosynflux_ivar')[:,rfilter]))
goods2n = (rs2n >= sncut)

del rs2n

notsky     = np.array(notsky)
notskyinds = np.arange(0, len(spall))[notsky]

wavemin = spall.field('wavemin')
wavemax = spall.field('wavemax')
z       = spall.field('z')

correctedmin = wavemin/(1. + z)
correctedmax = wavemax/(1. + z)

del wavemin
del wavemax
del z

maxwavelength = 9186.
minwavelength = 3856.

goodwavelengths = np.bitwise_and(correctedmin <= minwavelength, 
				correctedmax >= maxwavelength)
del correctedmin
del correctedmax

#logical step to select out indices of spall file that make all wanted cuts
spall2 = spall[np.bitwise_and(np.bitwise_and(goods2n, np.bitwise_and(notsky, lowz)), goodwavelengths)].copy()
uniqplates = np.unique(spall2.field('plate'))
spallhdulist.close()
pdb.set_trace()
del spall
del notsky
del lowz
del goods2n
del goodwavelengths
del spallhdulist

gc.collect()

"""
Sometimes you want to have a list comprehension refer to itself, but you can't because it isn't bound to a name until after it is fully constructed. However, the interpreter creates a secret name that only exists while the list is being built. That name is (usually) '_[1]', and it refers to the bound method 'append' of the list. This is our back door to get at the list object itself.
"""

flux = []
z    = []
invvar = []
wave0 = []
wave1 = []
num = 0

#loop through all wanted indices of spall file and grab spectrum, invvar, etc. from the spplate files

for p in np.arange(len(uniqplates)):
	nowplatestf   = spall2.field('plate') == uniqplates[p]
	nowplatesindx = np.where(nowplatestf)
	nowmjd        = np.unique(spall2[nowplatesindx].field('mjd'))
	spplatefilenameprefix = topdir + '/' + run2d + '/' 
       	for m in np.arange(len(nowmjd)):        #len(nowplates)):
		with pf.open(spplatefilenameprefix+str(uniqplates[p])+'/spPlate-'+str(uniqplates[p])+'-'+str(nowmjd[m])+'.fits', memmap=True) as spallhdulist:
			zanshdulist  = pf.open(spplatefilenameprefix+str(uniqplates[p])+'/'+run1d+'/spZbest-'+str(uniqplates[p])+'-'+str(nowmjd[m])+'.fits', memmap=True)
			zans         = zanshdulist[1].data
			spall        = spallhdulist[0].data
			spall1       = spallhdulist[1].data
			wantedfiberindx  =  spall2[np.where(np.bitwise_and(spall2.field('plate')==uniqplates[p],spall2.field('mjd')==nowmjd))].field('fiberid')
			for fib in np.arange(len(wantedfiberindx)):
				flux.append(np.array(spall[wantedfiberindx[fib]-1,:]).copy())
				invvar.append(np.array(spall1[wantedfiberindx[fib]-1,:]).copy())
				wave0.append(spallhdulist[0].header['COEFF0'])
				wave1.append(spallhdulist[0].header['COEFF1'])
				z.append(zans[wantedfiberindx[fib]-1].field('z'))
			#print np.shape(wantedfiberindx)
			del zans
			del spall
			del spall1
			del wantedfiberindx
			num += 1
			print num
			zanshdulist._HDUList__file._File__file.close()
			spallhdulist._HDUList__file._File__file.close()
			del zanshdulist
			del spallhdulist
			gc.collect()
	del nowplatestf
	del nowplatesindx
	del nowmjd
	gc.collect()

wave0 = np.array(wave0)
wave1 = np.array(wave1)
z     = np.array(z)
#			if fib gt 0:

#unredshift spectra
maxwavelength = 9186
minwavelength = 3856.
fluxsize = len(flux)

import pdb
deredloglambda0 = wave0 - np.log(1. + z)
length = np.zeros(len(flux))

#since all different lengths, determine largest, fill, then only select out nonzero entries for fit
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
chisq        = np.zeros(len(flux))

#resample spectra at single wavelength spectrum defined above
smoothing_parameter = 3.0
spline_order = 3
number_of_knots = -1

for p in range(len(flux)):
    nonzero = np.where(wavevector[p,:] != 0.)
    fitcoeff = cspline1d(flux[p], lamb=smoothing_parameter)
    newflux[p,:] = cspline1d_eval(fitcoeff, newwave, dx=wave1[p], x0 = wavevector[p,0])
    oldfit = cspline1d_eval(fitcoeff, wavevector[p,nonzero][0], dx=wave1[p], x0 = wavevector[p,0])
    chisq[p] = np.sum(np.sqrt((oldfit - flux[p])**2.*invvar[p]))/np.shape(flux[p])[0]

filename = 'pcaspectra_rest.fits'
pf.writeto(filename, newflux, clobber=True)
pf.append(filename, newwave)
pf.append(filename, z)

t1 = time.time()
print t1-t0

