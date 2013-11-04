# export the detection results into the web database

from ex import *
import sdss.utils as utils

def usage():
    print('''
import the object level detection results into the web database

python web_import_scores.py --input=input_score_files [--portion=0.2]
''')
    sys.exit(1)

def main(input_files, portion = 0.2):
    db_name = 'iii_web.db3'

    if True:# not new_db:
        log.info('Fetching newest DB...')
        cmd = 'rsync -avP sdss:/home/lxiong/www/db/%s .' % (db_name)
        log.info(cmd)
        if os.system(cmd) != 0:
            raise RuntimeError('Failed to retrieve the old web db')
    else:
        log.info('Creating new DB...')
        os.system('mv %s %s.bak' % (db_name, db_name))
        os.system('sqlite3 -init create_db.sql %s .exit' % (db_name))

    # make backup
    backup_name = '/auton/home/lxiong/sdss-www-snapshot/db_history/%s.%s.tar.bz' % (db_name, utils.GetStamp())
    os.system("tar -jcf {0} {1}".format(backup_name, db_name))
    log.info('Old DB backed up: {0} -> {1}'.format(
            db_name, backup_name))

    input_files = ExpandWildcard(input_files)
    log.info('Importing scores from %d files...' % len(input_files))
    db = GetDB(db_name, 1000)

    # clear the db, except human input
    # log.info('!!! Cleaning DB...')
    # db.execute('DELETE FROM object_info;')
    # db.execute('DELETE FROM object_score;')

    log.info('Droping index...')
    db.execute('DROP INDEX IF EXISTS IDX_INFO_PMF_DATE;')
    db.execute('DROP INDEX IF EXISTS IDX_SCORE_RID_SCORE;')
    db.execute('DROP INDEX IF EXISTS IDX_SCORE_PMF;')

    for input_file in input_files:
        data = LoadPickles(input_file)

        run_id = data['run_id']
        scores = data['scores']
        sidx = np.argsort(scores)[::-1]
        n = int(scores.size*portion)
        sidx = sidx[:n]
        log.info('Handling RunID %d' % run_id)

        scores = scores[sidx]
        pmfs = data['PMF'][sidx]
        sdss_id = data['sdss_id'][sidx]
        spec_cln = data['spec_cln'][sidx]
        cla, subcla = (data['class'][sidx], data['subclass'][sidx])
        z, ra, dec = (data['z'][sidx], 
                      data['ra'][sidx], 
                      data['dec'][sidx])
        stamp = data['stamp'][sidx]
        mjd = (pmfs/10000) % 100000

        # add new objects
        opmfs = db.execute('SELECT pmf FROM object_info').fetchall()
        opmfs = arr([a[0] for a in opmfs], dtype = int64)
        log.info('Checking the presence of new objects')
        if len(opmfs) == 0:
            filt = ones(n, dtype = bool)
        else:
            filt = EncodeArray(pmfs, opmfs) < 0
        if filt.any():
            log.info('Adding %d/%d new objects' % (filt.sum(),len(filt)))
            db.executemany('''INSERT INTO object_info 
VALUES (?,?,?,?,?,?,?,?,?,?)''', 
                           zip(pmfs[filt].tolist(), 
                               sdss_id[filt].tolist(),
                               spec_cln[filt].tolist(),
                               cla[filt].tolist(), 
                               subcla[filt].tolist(),
                               z[filt].tolist(), 
                               ra[filt].tolist(), 
                               dec[filt].tolist(),
                               stamp[filt].tolist(),
                               mjd[filt].tolist()))
        else:
            log.info('No new objects')

        # update object info
        log.info('Exporting scores from {1} to {2}'.format(
                n, input_file, db_name))

        # clear old result
        log.info('Deleting old rows')
        db.execute('DELETE FROM object_score WHERE run_id={0}'.format(run_id))
        
        cmd = 'INSERT INTO object_score VALUES (?,?,?,?)'
        rows = [(int(pmfs[i]), run_id, float(scores[i]), i + 1) 
                for i in range(n)]
        log.info('Inserting %d new scores' % (len(rows)))
        db.executemany(cmd, rows)
        db.commit()

    log.info('Creating index')
    db.execute('CREATE INDEX IDX_INFO_PMF_DATE ON object_info (pmf,stamp,mjd);')
    db.execute('CREATE INDEX IDX_SCORE_RID_SCORE ON object_score (run_id,score);')
    db.execute('CREATE INDEX IDX_SCORE_PMF ON object_score (pmf);')

    db.close()

    log.info('Sending DB to web sever...')
    os.system('chmod 777 ./%s' % db_name)
    cmd = 'rsync -avP ./%s sdss:/home/lxiong/www/db/' % (db_name)
    log.info(cmd)
    if os.system(cmd) != 0:
        raise RuntimeError('Failed to upload the new web db')

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], 
                   ['input=','portion='], 
                   usage)

    input_files = opts['--input']
    portion = float(opts.get('--portion', 0.2))

    main(input_files, portion)
