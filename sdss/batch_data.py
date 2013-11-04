# prepare all the data.

from ex import *

nproc = 4
spec_cln = 3

chunk_size=500 # limit the memory of each process
for i in range(6):
    check_call(['python', 
                  '~/h/python/sdss/dr7_assemble_data.py', 
                  '--nproc=' + nproc, 
                  '--selector="sciencePrimary=1 and specClass=%d and plate between %d and %d"' % (spec_cln, i*chunk_size, (i+1)*chunk_size - 1)])

if spec_cln == 1:
    snr_thresh = 10
    mag_thresh = 15.5
else: # use a loose filter to protect spatial clusters
    snr_thresh = 5
    mag_thresh = 15
check_call(['python',
              '~/h/python/sdss/dr7_compact.py',
              '--nproc=' + nproc,
              '--snr_thresh=' + snr_thresh,
              '--mag_thresh=' + mag_thresh])

check_call(['python',
              '~/h/python/sdss/dr7_repair.py',
              '--nproc=' + nproc])
