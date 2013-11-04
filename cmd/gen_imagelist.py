from ex.common import *
from ex.ioo import *

if len(sys.argv) < 3:
    print('''generated a html list of input images
    python gen_imagelist.py output_html image_height images(wildcard)
    ''')
    sys.exit(1)

output = sys.argv[1]
height = sys.argv[2]
files = sys.argv[3:]

if os.path.exists(output):
    print 'Output file already exists.'
    sys.exit(1)

print 'Generating a list for {0} images with height {1}'.format(len(files),height)
if len(files) > 100:
    print "Too many images. Can't process."
    exit

urllist = []
for f in files:
    urllist.append('<a href="{0}" alt="{0}"><img src="{0}" height="{1}" border="0" /></a>'.format(f,height))

html='\n'.join(urllist)
html='<html><body>' + html + '</body></html>'

SaveText(output, html)
print 'Result saved to {0}'.format(output)
