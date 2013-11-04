from ex import *

import report

def usage():
    print('''
Generate report given the matlab data file. This program only work for the BOSS data.

For PAD results, the data file should contain the following variables:
mpf: an matrix of objects' (mjd,plate,fiber). one row per object.
scores: the scores for each object.
report_type: should be 'pad'

python --score_files=
''')
    sys.exit(1)

def GenObjFigure(mpf_str, spectrum_size):
    spectrum_url = 'http://www.autonlab.org/sdss/boss_img/png/spec-{0}.png'.format(mpf_str)
    
    html='''
<a href="{0}" target="_blank"><img src="{0}" border="0" width="{1}"></a>
'''.format(spectrum_url, spectrum_size)

    return html

def GenPADReport(mpfs, scores, nobj = 50):

    sidx = argsort(scores)[::-1]
    mpfs = mpfs[sidx]
    scores = scores[sidx]
    n = scores.size

    html_an='<html><body>\n'
    for i in range(nobj):
        mpf_str = '%s-%s-%s' % (str(mpfs[i][1]).zfill(4), str(mpfs[i][0]).zfill(5), str(mpfs[i][2]).zfill(3))
        html_an+='<div style="float:left">{0}<br><small>ID={1}<br>Score={2:.3e}</small></div>'.format(
            GenObjFigure(mpf_str, 300), 
            mpf_str, float(scores[i]))
    html_an+='</body></html>'

    html_all='<html><body>\n'
    for i in range(0, n, int(round(n*1./nobj))):
        mpf_str = '%s-%s-%s' % (str(mpfs[i][1]).zfill(4), str(mpfs[i][0]).zfill(5), str(mpfs[i][2]).zfill(3))
        html_all+='<div style="float:left">{0}<br><small>ID={1}<br>Score={2:.3e}</small></div>'.format(
            GenObjFigure(mpf_str, 300), 
            mpf_str, float(scores[i]))
    html_all+='</body></html'

    return (html_an, html_all)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], ['score_files='], 
                   usage)

    score_files = ExpandWildcard(opts['--score_files'])

    for score_file in score_files:
        log.info('Reading report info from ' + score_file)
        data = LoadMat(score_file)
        tag = score_file[score_file.find('['):(score_file.rfind(']')+1)]
        report_type = ''.join(data['report_type'][0])
        check(report_type in ['pad', 'gad'], 'unknown detection type')
        tag = "[{0}]{1}".format(report_type, tag)

        if report_type == 'pad':
            r_an, r_all = GenPADReport(data['mpf'], data['scores'].ravel())
            SaveText('report_{0}_anomaly.html'.format(tag),r_an)
            SaveText('report_{0}_all.html'.format(tag),r_all)
        elif report_type == 'gad':
            raise ValueError('not implemented')
        else:
            raise ValueError('unknown report type')
