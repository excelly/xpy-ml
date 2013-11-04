# export the classification results into the web database

from ex.common import *
from ex.ioo import *
import ex.array as ea

def usage():
    print('''
import the object classification results into the web database

python web_import_classification.py --input=input_classified_files
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['input='], usage)
    input_files=ExpandWildcard(opts['--input'])

    log.info('Importing classification from {0}'.format(
            input_files))

    log.info('Copying DB to local...')
    os.system('scp sdss:www/sdss-backend-db/sdss_web.db3  /tmp/sdss/')

    output_db='/tmp/sdss/sdss_web.db3'
    log.info('Importing classification...')
    db=GetDB(output_db, 1000)
    
    for input_file in input_files:
        data=LoadPickles(input_file)
        spec_ids=data['specObjID']
        predicted=data['predicted']
        prob=data['prob']
        run_id=data['runID']
        n=spec_ids.size

        log.info('Exporting {0} predictions from {1} to {2}'.format(n, input_file, output_db))

        # clear old result
        log.info('Deleting old rows')
        db.execute('delete from object_class where runID={0}'.format(run_id))
        
        cmd='INSERT INTO object_class VALUES (?,?,?,?)'
        rows=[(int(spec_ids[i]),predicted[i],float(prob[i]),run_id)
              for i in range(n)]
        log.info('Inserting new rows')
        db.executemany(cmd, rows)
        db.commit()

    db.close()

    log.info('Copying DB to host...')
    os.system('scp /tmp/sdss/sdss_web.db3 sdss:www/sdss-backend-db/sdss_web.db3.new')

    log.info('Done.')
