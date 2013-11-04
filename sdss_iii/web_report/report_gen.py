from ex import *

import report

def usage():
    print('''
Generate report given the matlab data file. This program only work for the BOSS data.

For PAD results, the data file should contain the following variables:
pmf: an matrix of objects' (plate,mjd,fiber). one row per object.
scores: the scores for each object.
report_type: should be 'pad'

python --score_files=
''')
    sys.exit(1)

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
            r_an, r_all = GenPADReport(data['pmf'], data['scores'].ravel())
            SaveText('report_{0}_anomaly.html'.format(tag),r_an)
            SaveText('report_{0}_all.html'.format(tag),r_all)
        elif report_type == 'gad':
            raise ValueError('not implemented')
        else:
            raise ValueError('unknown report type')
