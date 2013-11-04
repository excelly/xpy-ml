#! /bin/csh -f

set path = ($path $PWD)

setenv SCRIPT_DIR $PWD

echo $SCRIPT_DIR

#set $BOSS_SPECTRO_REDUX to top directory
setenv BOSS_SPECTRO_REDUX $PWD'/data'
exit(0)
echo $BOSS_SPECTRO_REDUX
mkdir $BOSS_SPECTRO_REDUX

#set $RUN2D to current 2d pipeline version (v5_4_31)
setenv RUN2D v5_5_0

#set $RUN1D to current 1d pipeline version (in all of time i have known = 2d) (v5_4_31)
setenv RUN1D v5_5_0

setenv RSYNC_PASSWORD 4-surveys

#grab the most recent spAll file
#within topdir 

cd $BOSS_SPECTRO_REDUX

echo `pwd`

# rm logfile.txt

# wget -nH --cut-dirs=2 -np --user=sdss3 --password=4-surveys \
# 	http://data.sdss3.org/sas/bossredux/spAll-v5_5_0.fits
	
# rsync -aLrvz --include "*/" \
#         --include "spPlate*fits" --include "spZ*fits" --include "photo*fits" \
#         --log-file="logfile.txt" --exclude "*" \
#         rsync://sdss3@data.sdss3.org/sas/bosswork/groups/boss/spectro/redux/v5_5_0/ v5_5_0/

# backup the log
#set now = `date +%y%m%d-%H%M`
#cp logfile.txt logfile_$now.txt

cd $SCRIPT_DIR
python makepcafits.py

#out pop pcaspectra_rest.fits
#HDU 0 = spectra
#HDU 1 = table ['z', 'plate', 'mjd', 'fiber', 'class', 'subclass', 'length']
#HDU 2 = magnitudes
#HDU 3 = wavelength
#HDU 4 = inverse variance 
