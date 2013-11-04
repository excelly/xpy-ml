import os
import sys
from glob import glob

if len(sys.argv) < 3:
    print('''join the specified mp4 files
    python join_mp4.py output inputs(wildcard)
    ''')
    sys.exit(1)

output = sys.argv[1]
inputs = sys.argv[2:]

if len(inputs) == 1 and inputs[0].find('*') > 0:
	inputs = glob(inputs[0])

inputs = sorted(inputs)
cmd = 'MP4Box'
for part in inputs:
	cmd += ' -cat ' + part
cmd += ' ' + output
	
print cmd
os.system(cmd)
