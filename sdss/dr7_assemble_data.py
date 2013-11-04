from ex import *
import ex.pp.mr as mr
from ex.plott import *

from ex.ioo.FITS import FITS
import sdss.Spec as Spec
import sdss.settings as settings

class PlateReducer(mr.BaseReducer):
    '''assemble data of a palte
    '''

    def __init__(self, fields, rebin_c0, rebin_c1, rebin_nbin, zmin, zmax, remove_sky_absorption, lines):
        mr.BaseReducer.__init__(self, 'Plate Assembler', True)

        self.rebin_c0 = rebin_c0
        self.rebin_c1 = rebin_c1
        self.rebin_nbin = rebin_nbin
        self.z_min = zmin
        self.z_max = zmax
        self.fields = fields
        self.remove_sky_absorption = remove_sky_absorption
        self.lines = lines if lines is not None else Spec.default_lines
        self.output_dir = './src/'
        MakeDir(self.output_dir);

    def Reduce(self, key, vals):
        '''assemble specs for a plate together.
        key: the plate id
        vals: the list of specs

        returns # objects in this plate
        '''

        plate = str(key).zfill(4)
        input_list = vals
        output_file = "{0}/{1}.pkl.bz".format(
            self.output_dir, plate)

        # if the file has already been processed
        if os.path.exists(output_file): 
            log.info('Skipping {0}'.format(plate))
            return len(input_list)

        n = len(input_list)
        log.info("Processing plate {0} with {1} files".format(
                plate, n))
        if n == 0:
            log.warn('Empty plate')
            return 0

        # each element in list is:
        spec_list = []
        for record in input_list:
            spec = Spec.Spec(record[-1], Spec.default_sf_names, self.lines)

            # filtering
            if spec.LF is None:
                log.debug('{0} skipped: lack of line features'.format(spec.MPF))
                continue
            if spec.SF['Z'] < self.z_min or spec.SF['Z'] > self.z_max:
                log.debug('{0} skipped: z = {1}'.format(spec.MPF, spec.SF['Z']))
                continue

            if self.remove_sky_absorption:
                try: 
                    spec.RemoveSkyLines()
                except Exception as e:
                    log.warn('{0} skipped: failed to remove skylines:\n{1}'.format(spec.MPF, e))
                    continue
            
            try:
                # fig = figure()
                # subplot(fig,121)
                # spec.Plot()

                spec.ChangeFrame()
                spec = spec.ReBin(self.rebin_c0, self.rebin_c1, self.rebin_nbin)

                # subplot(fig,122)
                # spec.Plot()
            except Exception as e:
                log.warn('{0} skipped: failed to rebin:\n{1}'.format(spec.MPF,e))
                continue

            for i in range(len(fields)):
                spec.SF[fields[i]] = record[i]

            spec.SF['rebin_c0'] = rebin_c0
            spec.SF['rebin_c1'] = rebin_c1

            # print spec.SF
            # show()

            spec_list.append(spec)
            
        if len(spec_list) > 0:
            data = Spec.Spec.Assemble(spec_list, self.lines)
            SavePickle(output_file, data)

        log.info("Finished plate {0} with {1} objects".format(
                plate, len(spec_list)))

        return len(spec_list)

    def Aggregate(self, pairs):
        '''return the total objects processed
        '''

        keys, counts = unzip(pairs)
        return sum(counts)

def GetFITSPath(folder, mjd, plate, fiber):
    plate = str(plate).zfill(4)
    fiber = str(fiber).zfill(3)
    return "{0}/data/{2}/spSpec-{1}-{2}-{3}.fit".format(
        folder, mjd, plate, fiber)

def usage():
    print('''
assemble data from the sdss dr7 raw data. run this program in the
top-level directory (e.g. dr7_1) of the data set.

python dr7_assemble_data.py  [--selector="sciencePrimary=1 and specClass=1"] [--nbin=nbin] [--zrange=zmin,zmax] [--nproc={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()

    opts = CmdArgs(sys.argv[1:], ['nproc=', 'selector=', 'zrange=','nbin='], usage)

    nproc = opts.get('--nproc', 1)
    selector = opts.get('--selector', "sciencePrimary=1 and specClass=1")
    rebin_nbin = int(opts.get('--nbin', '500'))
    zrange = opts.get('--zrange', '-1e-3,0.36')
    input_dir = settings.sdss_dir

    log.info("Assembling SDSS data from {0} using {1} processes".format(input_dir, nproc))

    remove_sky_absorption = True
    # figure out the correct way of binning according to the zrange
    # the spectrum from sdss is from 3830A to 9200A
    # if the zrange is [0,0.36], then c0 = 3.5832, c1*rebin_nbin = 0.2464
    zrange = zrange.split(',')
    zmin, zmax = [float(r) for r in zrange]
    
    rebin_c0, rebin_c1 = Spec.Spec.ComputeCoeffs(
        (3830,9200), [float(z) for z in zrange], rebin_nbin)

    # jake's settings
    # rebin_c0 = 3.583   
    # rebin_c1 = 0.2464/rebin_nbin
    # rebin_nbin = 500
    # zmin = -1e-3
    # zmax = 0.36

    log.info('Rebin: raw wave in [%0.1f,%0.1f], c in [%0.5f,%0.5f], z in [%0.2f,%0.2f], No O line = %s' % (
            10**rebin_c0, 10**(rebin_c0 + rebin_c1*rebin_nbin),
            rebin_c0, rebin_c0 + rebin_c1*rebin_nbin,
            zmin, zmax, remove_sky_absorption))

    # fields to extract from the SDSS DB
    fields = ['specObjID', 'mjd', 'plate', 'fiberID', 'bestObjID', 'specClass', 'fiberMag_g', 'fiberMag_r', 'fiberMag_i', 'fiberMag_u', 'fiberMag_z']

    # retrieving the plate list
    log.info('Retrieving object list...')
    db = GetDB(input_dir + '/sdss.db3', 1000)
    cmd = "SELECT {0}, fits_url from object_list where {1}".format(','.join(fields), selector)
    cur = db.execute(cmd)

    rows = [list(r) for r in cur]
    plates = [r[2] for r in rows]
    # update the path to the fits file
    for r in rows:
        r[-1] = GetFITSPath(input_dir, r[1], r[2], r[3])
    log.info('{0} objects found'.format(len(rows)))

    reducer = PlateReducer(fields, rebin_c0, rebin_c1, rebin_nbin, zmin, zmax, remove_sky_absorption, {1215.67:'Ly\\d\\ga'})
    engine = mr.ReduceEngine(reducer, nproc)

    jobs = zip(plates, rows)
    nobjs = engine.Start(jobs)

    log.info("{0} objects processed".format(nobjs))
