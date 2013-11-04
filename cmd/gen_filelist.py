from ex.common import *
from ex.ioo import *

if len(sys.argv) < 3:
    print('''generated a html list of input files
    python gen_filelist.py output_file files(wildcard)
    ''')
    sys.exit(1)

output = sys.argv[1]
files = sys.argv[2:]

if os.path.exists(output):
    print 'Output file already exists.'
    sys.exit(1)

print 'Generating a list for {0} files...'.format(len(files)))
filelist=[]
for f in files:
    filelist.append('<a href="{0}">{0}</a><br>'.format(f))

html='\n'.join(filelist)
html='<html><body>' + html + '</body></html>'

SaveText(output, html)
log.info('Result saved to {0}'.format(output))
