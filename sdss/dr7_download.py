import urllib

from ex import *
import ex.pp.mr as mr

class Mapper(mr.BaseMapper):
    '''download spec files from the sdss website
    '''

    def __init__(self, output_dest):
        mr.BaseMapper(self, 'SDSS DR7 downloader', output_dest)

    def Map(self, key, val):
        '''download the url. return (output_file, successful or not).
        '''

        url=val
        filename=url.split('/')[-1]
        output_file="{0}/{1}".format(self.output_dest, filename)

        # if the file has already been processed
        if os.path.exists(output_file): 
            log.info('Skipping {0}'.format(filename))
            return (output_file, True)

        try:
            urllib.urlretrieve(url, output_file)
        except Exception as ex:
            log.warn("Download of {0} failed. Try again later.\nError: {1}".format(
                    filename, ex))
            return (output_file, False)

        log.info('{0} downloaded'.format(filename))
        return (output_file, True)

def usage():
    print('''
download spec files from SDSS in the list database.

python [--input=list_db] [--output={output directory}] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts=getopt(sys.argv[1:], ['output=','input=', 'poolsize=', 'help'], usage)

    output_dir=os.path.abspath(opts.get('--output', os.getcwd()))
    list_db=opts['--input']
    poolsize=opts.get('--poolsize', 1)

    log.info('Connecting to DB {0}'.format(list_db))
    db=sql.connect(list_db)

    cur=db.execute('select distinct plate from sdss_list_all')
    plate_list=[row[0] for row in cur]
    log.info('Processing {0} plates'.format(len(plate_list)))

    tot_n=0;
    for plate in plate_list:
        # create the directory
        output_sub_dir='{0}/{1}'.format(output_dir, str(plate).zfill(4))
        if not os.path.exists(output_sub_dir): 
            os.mkdir(output_sub_dir)

        cur=db.execute('select fits_url from sdss_list_all where plate={0}'.format(
                plate))
        url_list=[row[0] for row in cur]
        
        log.info('Downloading {0} files for plate {1}'.format(len(url_list), plate))

        mapper=Mapper(output_sub_dir)
        engine=mr.MapEngine(mapper, poolsize)
        jobs=zip(url_list, url_list)

        results=engine.Start(jobs)
        n=sum([r[1] for r in results])
        
        log.info('{0} files downloaded.'.format(n))
        tot_n+=n

    log.info('{0} files downloaded in total'.format(tot_n))
