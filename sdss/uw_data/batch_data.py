import sys
import os

poolsize=6

# if os.system('python ~/h/python/cmd/map_files.py --input=./src/*.dat --output=./expanded/ --module="sdss.mr_expand_fits" --poolsize={0}'.format(poolsize)) != 0:
#     sys.exit(1)

# if os.system('python ~/h/python/cmd/map_files.py --input=./expanded/*.pkl.bz --output=./integrated/ --module="sdss.mr_integrate_spec" --poolsize={0}'.format(poolsize)) != 0:
#     sys.exit(1)

poolsize=4

# if os.system('python ~/h/python/cmd/map_files.py --input=./integrated/*.pkl.bz --output=./compact/ --module="sdss.mr_compact_data" --poolsize={0} --groupsize=70'.format(poolsize)) != 0:
#     sys.exit(1)

if os.system('python ~/h/python/cmd/map_files.py --input=./compact/*.pkl --output=./prepared/ --module="sdss.mr_prepare_data" --poolsize={0}'.format(poolsize)) != 0:
    sys.exit(1)

if os.system('python ~/h/python/sdss/repair_spectrum.py --input=./prepared/*.pkl --output=./repaired/ --poolsize={0}'.format(poolsize)) != 0:
    sys.exit(1)

print 'Success!'
