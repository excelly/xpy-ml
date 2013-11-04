import numpy as np
import pdb
import pyfits as pf
import os
import matplotlib.pyplot as plt

topdir = os.getenv('BOSS_SPECTRO_REDUX')
run2d  = os.getenv('RUN2D')
run1d  = os.getenv('RUN1D')

filename = 'pmf.lst'

nameList = [s.strip() for s in open(filename).readline().split(',')]
names    = dict(zip(nameList, range(len(nameList))))

result = np.loadtxt(filename, skiprows=1,delimiter=',', \
                    dtype={'names'  : nameList, \
                           'formats':('i4','i4','i4')})

mjd   = result['MJD']  
plate = result['Plate']
fiber = result['Fiber']

number_of_plots = len(mjd)

for i in range(0, number_of_plots):
	index = i

	spplatefilenameprefix = topdir + '/' + run2d + '/' 
	spplatefilename    = spplatefilenameprefix+str(plate[index])+'/spPlate-'+          str(plate[index])+'-'+str(mjd[index])+'.fits'
	spzbestfilename    = spplatefilenameprefix+str(plate[index])+'/'+run1d+'/spZbest-'+str(plate[index])+'-'+str(mjd[index])+'.fits'
	photoplatefilename = spplatefilenameprefix+str(plate[index])+'/photoPlate-'+       str(plate[index])+'-'+str(mjd[index])+'.fits'

	spplatehdulist = pf.open(spplatefilename, memmap=True)
	zbesthdulist   = pf.open(spzbestfilename, memmap=True)
	photohdulist   = pf.open(photoplatefilename, memmap=True)

	zans         = zbesthdulist[1].data
	spplate      = spplatehdulist[0].data
	spplate1     = spplatehdulist[1].data

	flux           = spplate[fiber[index]-1,:].copy()
	invvar         = spplate1[fiber[index]-1,:].copy()
	wave0          = spplatehdulist[0].header['COEFF0']
	wave1          = spplatehdulist[0].header['COEFF1']
	length         = spplatehdulist[0].header['NAXIS1']
	sky            = spplatehdulist[6].data[fiber[index]-1,:].copy()
	z              = zans[fiber[index]-1].field('z')
	classification = zans[fiber[index]-1].field('class')
	subclass       = zans[fiber[index]-1].field('subclass')
	eigenspectrum  = zbesthdulist[2].data[fiber[index]-1,:].copy()

	invvarzeros = np.where(invvar == 0.)
	invvar[invvarzeros] = 1e-5

	wavevector = np.power(10., wave0 + np.arange(length)*wave1)
	plt.figure(1)
	err = 1./np.sqrt(invvar)
	plt.plot(wavevector, err, '-r')
	plt.plot(wavevector, sky, '-y')
	plt.plot(wavevector, eigenspectrum, '-b')
	plt.plot(wavevector, flux, '-k')
	plt.legend(('Error', 'Sky', 'Best-Fit Eigen-Spectrum', 'Data'), loc=1)
	plt.xlabel('Observed Wavelength [$\AA$]')
	plt.ylabel('Flux [$10^{-17}$ ergs/s/$\mathrm{cm^2}$/$\AA$]')
	plt.title('Plate '+str(plate[index])+'   Fiber '+str(fiber[index])+'   MJD '+str(mjd[index]))
	xmin = np.min(wavevector)
	xspan = np.max(wavevector) - xmin
	fluxmin = np.min(flux)
	errmin  = np.min(err)
	ymin = np.min([fluxmin, errmin])
	ymax = np.max(flux)
	yspan = ymax - ymin
	plt.ylim(ymin*0.9, ymax*1.1)
	plt.text(xspan*0.6 + xmin, yspan*0.65 + ymin, 'Pipeline Classification = ' + classification)
	if subclass.__ne__(''):
		plt.text(xspan*0.6 + xmin, yspan*0.6 + ymin, 'Subclassification = ' + subclass)
	plt.text(xspan*0.6 + xmin, yspan*0.7 + ymin, 'Redshift = ' + str(z))
#	plt.show()

	plotfilename = './figures/Figure-' + str(plate[index]) + '-' + str(mjd[index]) + '-' + str(fiber[index]) + '.png'
	print("%d/%d: %s" % (index, number_of_plots, plotfilename))
	plt.savefig(plotfilename, facecolor='w', edgecolor='k', format='png')
	plt.clf()

