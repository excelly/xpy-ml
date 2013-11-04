from ex import *
from ex.ioo import *

import sdss.utils as utils

def usage():
    print '''
fetch_download.py working_dir [stamp](current time) [run](v_5_6_0)
'''
    sys.exit(0)

def main(working_dir, run, stamp):
    data_dir = '%s/data' % working_dir
    cwd = os.getcwd()
    os.chdir(data_dir)

    log.info('''SDSS III Download: 
Working dir: %s
Data dir   : %s
RUN        : %s
Stamp      : %s''' % (working_dir, data_dir, run, stamp))

    cmd = 'export RSYNC_PASSWORD=4-surveys; echo $RSYNC_PASSOWRD; rsync -zv --no-motd rsync://sdss3@data.sdss3.org/sas/bossredux/{0}/spAll-{0}.fits .'.format(run)
    log.info(cmd)
    if os.system(cmd) != 0:
        raise RuntimeError('Error downloading the spAll file')

    logfile = 'log/logfile_%s.txt' % stamp
    cmd = 'export RSYNC_PASSWORD=4-surveys; rsync --no-motd -aLzv --include "*/" --include "spPlate*fits" --include "spZ*fits" --include "photo*fits" --log-file="{0}" --exclude "*" rsync://sdss3@data.sdss3.org/sas/bosswork/groups/boss/spectro/redux/{1}/ plates/'.format(logfile, run)
    log.info(cmd)
    if os.system(cmd) != 0:
        raise RuntimeError('Error downloading the plate files')

    log.info('Download complete')
    os.chdir(cwd)

if __name__ == '__main__':
    if len(sys.argv) < 2: usage()
    InitLog()

    working_dir = os.path.abspath(sys.argv[1])
    stamp = sys.argv[2]
    run = sys.argv[3] if len(sys.argv) >= 4 else 'v_5_6_0'

    main(working_dir, stamp, run)
