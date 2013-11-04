from ex import *

import sdss_iii.settings as settings
import sdss.utils as utils

def GetSpectrumImage(pmf):
    p, m, f = pmf
    return 'http://www.autonlab.org/sdss/iii/spec_img/{0}/figure-{1}.png'.format(p, utils.PMF_DashForm(p, m, f))
    
def GenObjFigure(pmf, rd, img_height = 230):
    p,m,f = utils.PMF_N2S(pmf)
    
    html = '''
<a href="{0}" target="_blank">
<img src="{0}" border="0" height="{1}">
</a>
'''.format(utils.GetSkyImage(rd), img_height)
    
    html += '''
<a href="{0}" target="_blank">
<img src="{0}" border="0" height="{1}">
</a>
'''.format(GetSpectrumImage((p,m,f)), img_height)

    return html

def GenPADReport(scores, info, nobj = 50):

    sidx = argsort(scores)[::-1]
    nobj = min(len(scores), nobj)

    pmfs = info['PMF'][sidx]
    rds = zip(info['ra'][sidx], info['dec'][sidx])

    html_an = '<html><body>\n'
    for i in range(nobj):
        html_an += '''
<div style="float:left">
%s<br>
<small>
PMF=%ld, RA,Dec=(%0.3f,%0.3f)<br>
Score=%0.3f<br>
</small></div>
''' % (GenObjFigure(pmfs[i], rds[i]), 
       pmfs[i], rds[i][0], rds[i][1], float(scores[i]))
    html_an += '</body></html>'

    html_all = '<html><body>\n'
    for i in int32(linspace(0, len(scores)-1, nobj)):
        html_all += '''
<div style="float:left">
%s<br>
<small>
PMF=%ld, RA,Dec=(%0.3f,%0.3f)<br>
Score=%0.3f<br>
</small></div>
''' % (GenObjFigure(pmfs[i], rds[i]),
       pmfs[i], rds[i][0], rds[i][1], float(scores[i]))
    html_all += '</body></html'

    return (html_an, html_all)

def GenObjList(pmfs, rds):
    '''get a list of objects.
    '''

    parts = []
    for i in range(len(pmfs)):
        parts.append('''
<div style="float:left">
%s<br>
<small>
PMF=%ld, RA,DEC=(%0.3f,%0.3f)
</small>
</div>
''' % (GenObjFigure(pmfs[i], rds[i]), pmfs[i], rds[i][0], rds[i][1]))

    html = '<html><body>'
    html += '\n'.join(parts)
    html += '</body></html>'

    return html
