import sys
import os
from getopt import getopt
import logging as log
import multiprocessing as mp

import ex.util as eu
import base

eu.InitLog(log.DEBUG)

modifier=''
folder=''

drug_uid=None
cond_uid=None

def DoJob(drug_id):
    log.debug((modifier, folder, drug_id))

    db_cooc=base.GetDB(modifier, "COOC", folder)
    db_cooc.execute('PRAGMA temp_store=2')
    # d=[base.GetCOOCData(db_cooc, drug_uid, cond_uid, drug_id, cond_id) 
    #    for cond_id in cond_uid]
    d=base.GetCOOCData(db_cooc, drug_uid, cond_uid, drug_id) 
    db_cooc.close()

    n_record=sum([len(dd) for dd in d])
    log.debug('Result for drug {0}: {1}'.format(drug_id, n_record))
    return n_record

def usage():
    print('''generate contingincy table for the OMOP data base

    python gen_ctable.py --modifier={''} --folder={''} --help
    ''');
    sys.exit(1);

if __name__ == '__main__':
    try: 
        options=dict(getopt(sys.argv[1:], '', ['modifier=', 'folder=', 'help'])[0])
    except Exception as ex: 
        print(ex)
        usage()

    modifier=options.get('--modifier', '')
    if len(modifier) > 0: modifier = '_' + modifier
    folder=options.get('--folder', 'OSIM' + modifier) + '/'

    drug_uid=base.GetUniqueDrugs(None, modifier, folder)[0]
    cond_uid=base.GetUniqueConds(None, modifier, folder)[0]

    pool_size=min(mp.cpu_count() - 1, drug_uid.size, 3)
    pool_size=max(1, pool_size)

    log.info("Generating contingency table {0} x {1} using {2} processes...".format(drug_uid.size, cond_uid.size, pool_size))

    # log.info('Sequential run...')
    # results=map(DoJob, drug_uid[0:10])

    log.info('Parallel run...')
    p=mp.Pool(pool_size)
    results=p.map(DoJob, drug_uid[0:10])

    log.info("job done")
