from ex import *
import ex.pp.mr as mr
import settings

class Reducer(mr.BaseReducer):
    '''filter the data and pack them into bigger chunks
    '''

    def __init__(self, snr_thresh, badpixel_thresh, mag_thresh):
        mr.BaseReducer.__init__(self, 'DR7 Compact', True)
        self.output_dir = './compact/'
        self.snr_thresh = float(snr_thresh)
        self.badpixel_thresh = float(badpixel_thresh)
        self.mag_thresh = mag_thresh
        MakeDir(self.output_dir)

    def GetKey(self, filename):
        '''group the files according to their plate name
        '''

        filename = SplitFilename(filename)[0] # this is the plate id
        return filename[0:2]

    def Reduce(self, key, vals):
        input_files = vals
        n_files = len(input_files)

        output_file = "{0}/{1}.pkl".format(self.output_dir, key)
        if os.path.exists(output_file): 
            log.info('Skipping group {0}'.format(output_file))
            return n_files

        log.info("Processing {0} files for key {1} -> {2}".format(n_files, key, output_file))

        mpf = []
        vector_feat = []
        scalar_feat = []
        line_feat = []
        for f in input_files:
            data = LoadPickles(f)

            mpf.extend(data['MPF'])
            vector_feat.append(data['VF'])
            scalar_feat.append(data['SF'])
            line_feat.append(data['LF'])
            
        data_v = {}
        for key in vector_feat[0].keys():
            data_v[key] = AssembleMatrix(vector_feat, key)
        data_s = {}
        for key in scalar_feat[0].keys():
            data_s[key] = AssembleVector(scalar_feat, key)
        data_l = {}
        for key in line_feat[0].keys():
            data_l[key] = AssembleMatrix(line_feat, key)

        filt = self.Filter(data_s, data_v)
        mpf = arr(mpf)
        mpf = mpf[filt]
        for key in data_s.keys():
            data_s[key] = data_s[key][filt]
        for key in data_v.keys():
            data_v[key] = data_v[key][filt, :]
        for key in data_l.keys():
            data_l[key] = data_l[key][filt, :]

        log.info('{0} of {1} objects compacted'.format(sum(filt), len(filt)))

        SavePickle(output_file, {'MPF': mpf, 
                                 'SF': data_s, 
                                 'VF': data_v,
                                 'LF': data_l})

        return len(mpf)

    def Filter(self, sf, vf):
        '''filter out bad objects
        '''

        n, dim = vf['spectrum'].shape
        log.debug('{0} objects received.'.format(n))

        filter = np.ones(n, dtype = np.bool)

        # filter duplicates
        best_obj_id = sf['bestObjID']
        pairs = dict(zip(best_obj_id, range(len(best_obj_id))))
        if len(pairs) < len(best_obj_id):
            log.warn('{0} duplicates found'.format(len(best_obj_id) - len(pairs)))
            filter[:] = False
            for key, val in pairs.items():
                filter[val] = True

        # filter by portion of bad pixels
        n_bad_pixel = ((settings.bad_mask & vf['mask']) > 0).sum(1)
        filter &= n_bad_pixel*1.0/dim < 0.2
        log.debug('After bad pixel filtering: {0}'.format(filter.sum()))

        # filter by large amplitudes
        min_sp = vf['spectrum'].min(1)
        max_sp = vf['spectrum'].max(1)
        min_cont = vf['continuum'].min(1)
        max_cont = vf['continuum'].max(1)
        mean_cont = vf['continuum'].mean(1)
        filter &= (min_sp > -100) & (min_cont > -100) & (max_sp < 1e4) & (max_cont < 1e4) & (max_cont < mean_cont*10)
        log.debug('After amplitude filtering: {0}'.format(filter.sum()))

        # filter by Z warning
        # filter &= (settings.bad_z_warning & sf['Z_WARNIN']) == 0
        # log.debug('After Z warning filtering: {0}'.format(filter.sum()))

        # filter by Z status
        for bz in settings.bad_z_status:
            filter &= sf['Z_STATUS'] != bz
        log.debug('After Z status filtering: {0}'.format(filter.sum()))

        # filter by snr
        snr = emin((sf['SN_R'], sf['SN_G']))
        filter &= snr >= self.snr_thresh
        log.debug('After SNR filtering: {0}'.format(filter.sum()))

        # filter by mag. remove saturated objects.
        mag = emin((sf['MAG_G'], sf['MAG_R'], sf['MAG_I']))
        filter &= mag >= self.mag_thresh
        log.debug('After MAG filtering: {0}'.format(filter.sum()))

        return filter

    def Aggregate(self, pairs):
        '''return the total number of objects compacted
        '''

        return sum([p[1] for p in pairs])

def usage():
    print('''
filter and compact the dr7 source data. the source data are generated
by dr7_assemble_data.py. run this program in the top-level directory
(e.g. dr7_1) of the data set.

python dr7_assemble_data.py [--snr_thresh=10] [--badpixel_thresh=0.2] [--mag_thresh=15.5] [--nproc={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], 
                   ['nproc=','snr_thresh=', 
                    'badpixel_thresh=', 
                    'mag_thresh='], usage)

    nproc = opts.get('--nproc', 1)
    snr_thresh = opts.get('--snr_thresh', 10)
    badpixel_thresh = float(opts.get('--badpixel_thresh', 0.2))
    mag_thresh = float(opts.get('--mag_thresh', 15.5))

    input_files = ExpandWildcard('./src/*.pkl.bz')

    log.info("Compacting {0} SDSS files using {1} processes.".format(len(input_files), nproc))

    reducer = Reducer(snr_thresh, badpixel_thresh, mag_thresh)
    engine = mr.ReduceEngine(reducer, nproc)

    keys = [reducer.GetKey(f) for f in input_files]
    jobs = zip(keys, input_files)
    points = engine.Start(jobs)
    log.info('{0} objects compacted'.format(points))
