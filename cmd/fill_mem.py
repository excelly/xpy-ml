import sys
import numpy as np

target = int(sys.argv[1])
print 'Generating %d GB garbage...' % target

block_size = 1*1024*1024*1024/8
bulk = []
for i in range(target):
    bulk.append(np.zeros(block_size, dtype='float64'))

raw_input('done')
