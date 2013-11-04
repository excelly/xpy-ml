# export the detection results into the web database

from ex import *
import sdss_iii.settings as settings
import sdss.utils as utils

def usage():
    print('''
import the object similarities into the similarity database

python web_import_similarity.py --input=sim_files
''')
    sys.exit(1)

def main(input_files):
    db_name = 'iii_sim.db3'

    if True:# not new_db:
        log.info('Fetching newest DB...')
        cmd = 'rsync -avP sdss:/home/lxiong/www/db/%s .' % (db_name)
        log.info(cmd)
        if os.system(cmd) != 0:
            raise RuntimeError('Failed to retrieve the old similarity db')
    else:
        log.info('Creating new DB...')
        os.system('mv %s %s.bak' % (db_name, db_name))
        os.system('sqlite3 -init create_similarity_db.sql %s .exit' % (db_name))

    input_files = ExpandWildcard(input_files)
    log.info('Importing similarities from %d files...' % len(input_files))
    db = GetDB(db_name, 1000)

    log.info('Droping index')
    db.execute('DROP INDEX IF EXISTS IDX_FSC;')
    db.execute('DROP INDEX IF EXISTS IDX_FSP1;')

    for input_file in input_files:
        data = LoadPickles(input_file)

        edges = data['pairs']
        pmfs = data['pmf']
        feature = data['feature']
        sim_type = data['similarity']
        cln = int(data['spec_cln'])
        feat_code = settings.feature_code[feature.lower()]
        sim_code = settings.similarity_code[sim_type.lower()]
        n = edges.shape[1]

        pmf1 = pmfs[int32(edges[0])]
        pmf2 = pmfs[int32(edges[1])]
        sims = edges[2]

        # update object info
        log.info('Importing {0} similairties from {1} to {2}'.format(
                n, input_file, db_name))

        # clear old result
        log.info('Deleting old rows')
        db.execute('DELETE FROM object_similarity WHERE feature={0} AND similarity_type={1} AND spec_cln={2}'.format(feat_code, sim_code, cln))
        
        cmd = 'INSERT INTO object_similarity VALUES (?,?,?,?,?,?)'
        rows = [(feat_code, sim_code, cln, int(pmf1[i]), int(pmf2[i]), float(sims[i]))
                for i in range(n)]
        log.info('Inserting %d new similarities' % (len(rows)))
        db.executemany(cmd, rows)
        db.commit()

    log.info('Creating index')
    db.execute('CREATE INDEX IDX_FSC ON object_similarity (feature, similarity_type, spec_cln);')
    db.execute('CREATE INDEX IDX_FSP1 ON object_similarity (feature, similarity_type, pmf1);')

    db.close()

    log.info('Sending similarity DB to web sever...')
    os.system('chmod 777 ./%s' % db_name)
    cmd = 'rsync -avP ./%s sdss:/home/lxiong/www/db/' % (db_name)
    log.info(cmd)
    if os.system(cmd) != 0:
        raise RuntimeError('Failed to upload the new similarity db')

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], ['input='], 
                   usage)

    input_files = opts['--input']

    main(input_files)
