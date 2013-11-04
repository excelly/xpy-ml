from ex import *

import report

def usage():
    print('''
Generate report given the matlab data file. This program only work for SDSS DR7 data.

For GAD results, the data file should contain the following variables:
group_member_ids: a cell array. each cell for one cluster, containing member spec_ids.
scores: the scores for each cluster.
report_type: should be 'gad'

For PAD results, the data file should contain the following variables:
ids: an array of objects' spec_ids.
scores: the scores for each object.
report_type: should be 'pad'

python --score_files=
''')
    sys.exit(1)

def GetObjectInfo(db, spec_id):
    cmd = 'select ra, dec, z from object_list where specObjID={0};'.format(int(spec_id))
    cur = db.execute(cmd)
    return cur.fetchone()

def GenGADReport(db, score_data):
    member_ids = score_data['group_member_ids']
    member_ids = [mids[0] for mids in member_ids]
    scores = score_data['scores'].ravel()
    group_sizes = [len(mids) for mids in member_ids]
    M = scores.size;

    log.info('Looking up object info...')
    member_rdz = [arr([GetObjectInfo(db, m) 
                       for m in mids]) 
                  for mids in member_ids]

    log.info('Generating report...')
    clusters = []
    counter = 0;
    for m in range(M):
        clusters.append(arange(group_sizes[m]) + counter)
        counter += group_sizes[m]
    spec_ids = vstack(member_ids).ravel()
    rdz = vstack(member_rdz)
    return report.GenReportCluster(clusters,scores,spec_ids,rdz)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], ['score_files='], 
                   usage)

    score_files = ExpandWildcard(opts['--score_files'])

    db = GetDB('/auton/home/lxiong/data/sdss/dr7/sdss.db3')
    for score_file in score_files:
        log.info('Reading report info from ' + score_file)
        data = LoadMat(score_file)
        tag = score_file[score_file.find('['):(score_file.rfind(']')+1)]
        report_type = ''.join(data['report_type'][0])
        check(report_type in ['pad', 'gad'], 'unknown detection type')
        tag = "[{0}]{1}".format(report_type, tag)

        if report_type == 'pad':
            raise ValueError('not implemented')
        elif report_type == 'gad':
            r_an, r_all = GenGADReport(db, data);
            SaveText('report_{0}_anomaly.html'.format(tag),r_an)
            SaveText('report_{0}_all.html'.format(tag),r_all)
        else:
            raise ValueError('unknown report type')
    db.close()
