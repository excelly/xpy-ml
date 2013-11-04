#! /bin/csh -f

set path = ($path $PWD)

#set $BOSS_SPECTRO_REDUX to top directory
#setenv BOSS_SPECTRO_REDUX /astro/store/shared-scratch1/sdssspec
setenv BOSS_SPECTRO_REDUX /auton/home/lxiong/userdir/data/sdss/III/working_42

#set $RUN2D to current 2d pipeline version (v5_4_31)
setenv RUN2D v5_4_42

#set $RUN1D to current 1d pipeline version (in all of time i have known = 2d) (v5_4_31)
setenv RUN1D v5_4_42

#grab the most recent spAll file
#within topdir 

cd $BOSS_SPECTRO_REDUX

echo `pwd`

wget -nH --cut-dirs=2 -np --user=sdss3 --password=4-surveys \
	http://data.sdss3.org/sas/bossredux/spAll-v5_4_42.fits

rsync -aLrvz --password-file password.txt --include "*/" \
    --include "spPlate*fits" --include "spZ*fits" --include "photoPlate*fits" --exclude "*" \
    rsync://sdss3@data.sdss3.org/sas/bosswork/groups/boss/spectro/redux/v5_4_42/ v5_4_42/

	
#wget -nH --cut-dirs=6 -np -r-A "spPlate*fits,spZ*fits" \
#	--user=sdss3 --password=4-surveys \
#	http://data.sdss3.org/sas/bosswork/groups/boss/spectro/redux/v5_4_31
	
#run newandimproved.py
python makepcafits.py

#out pop pcaspectra_rest.fits
#HDU 0 = spectra
#HDU 1 = wavelength (in log10)
#HDU 2 = redshift
