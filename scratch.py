import sys
import os
from getopt import getopt
import glob

opts=dict(getopt(sys.argv[1:], '', 'a=')[0])

print opts
print glob.glob(opts['--a'])
