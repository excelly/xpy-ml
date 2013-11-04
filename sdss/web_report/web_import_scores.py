# export the detection results into the web database

from ex import *

def usage():
    print('''
import the object level detection results into the web database

python web_import_scores.py --input=input_score_files [--portion=0.2]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['input=','portion='], usage)
    input_files=ExpandWildcard(opts['--input'])
    portion=float(opts.get('--portion', 0.5))

    log.info('Copying DB to local...')
    MakeDir('/tmp/sdss')
    os.system('scp sdss:www/sdss-backend-db/sdss_web.db3  /tmp/sdss/')

    output_db='/tmp/sdss/sdss_web.db3'
    log.info('Importing scores...')
    db=GetDB(output_db, 1000)
    for input_file in input_files:
        data=LoadPickles(input_file)
        spec_ids=data['specObjID']
        scores=data['scores']
        n=scores.size
        run_id=data['run_id']

        log.info('Exporting {0} scores from {1} to {2}'.format(
                int(n*portion), input_file, output_db))

        # clear old result
        log.info('Deleting old rows')
        db.execute('delete from object_score where run_id={0}'.format(run_id))
        
        cmd='INSERT INTO object_score VALUES (?,?,?,?)'
        sidx=np.argsort(scores)[::-1]
        rows=[(int(spec_ids[sidx[i]]), run_id, float(scores[sidx[i]]), i + 1) 
              for i in range(int(n*portion))]
        log.info('Inserting new rows')
        db.executemany(cmd, rows)
        db.commit()

    db.close()

    log.info('Copying DB to host...')
    os.system('scp /tmp/sdss/sdss_web.db3 sdss:www/sdss-backend-db/sdss_web.db3.new')

    log.info('Done.')
