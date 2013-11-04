from ex.common import *
from ex.io.common import *

import ex.pp.mr as mr
import ex.array as ea
from ex.geo.kdtree import KDTree
import sdss_info as sinfo
import base

class Mapper(mr.BaseMapper):
    '''prepare the data so they can used by the reducer for
    processing. this module usually takes in results from compact
    data.
    '''

    def __init__(self, name, output_type, output_dest):
        mr.BaseMapper.__init__(self, name, output_type, output_dest)

        # parameters used by Filter()
        self.filter_snr_thresh=5
        self.filter_obj_type=['SPEC_GALAXY', 'SPEC_QSO']

    def Filter(self, vf, sf):
        '''filter objects
        '''

        n, dim=vf['SPECTRA'].shape

        # filter by portion of bad pixels
        n_bad_pixel=((sinfo.bad_mask & vf['MASK']) > 0).sum(1)
        filter = n_bad_pixel*1.0/dim < 0.1
        log.debug('After bad pixel filtering: {0}'.format(filter.sum()))

        # filter by Z warning
        filter &= (sinfo.bad_z_warning & sf['Z_WARNIN']) == 0
        log.debug('After Z warning filtering: {0}'.format(filter.sum()))

        # filter by Z status
        for bz in sinfo.bad_z_status:
            filter &= sf['Z_STATUS'] != bz
        log.debug('After Z status filtering: {0}'.format(filter.sum()))

        # filter by snr
        snr=ea.emin((sf['SN_R'], sf['SN_I'], sf['SN_G']))
        filter &= snr >= self.filter_snr_thresh
        log.debug('After SNR filtering: {0}'.format(filter.sum()))

        # filter large negative spikes
        min_amp=vf['SPECTRA'].min(1)
        max_amp=vf['SPECTRA'].max(1)
        filter &= (min_amp > -100)
        log.debug('After negative spike filtering: {0}'.format(filter.sum()))

        # filter by large amplitude
        max_sp=np.abs(vf['SPECTRA']).max(1)
        max_cont=np.abs(vf['CONTINUUM']).max(1)
        filter &= (max_sp < 1e4) & (max_cont < 1e4)
        log.debug('After large amplitude filtering: {0}'.format(filter.sum()))

        # filter by type
        classes=[sinfo.classes[o] for o in self.filter_obj_type]
        tf=np.zeros(n, dtype=np.bool)
        for cl in classes:
            tf |= sf['SPEC_CLN'] == cl
        filter &= tf
        log.debug('After type filtering: {0}'.format(filter.sum()))

        # filter duplicates
        ra=sf['RAOBJ']
        dec=sf['DECOBJ']
        location=np.vstack((ra, dec))
        tree=KDTree(location, 10)
        for i in range(n):
            if filter[i]:
                neighbors=tree.QueryRange((location[:,i], 1e-7), 'c')
                filter[neighbors]=False # remove duplicates
                filter[i]=True # don't remove itself

        return filter

    def Map(self, input_file):
        check(self.output_type == 'file', 'unsupported output type')

        output_file="{0}/{1}.pkl".format(
            self.output_dest, SplitFilename(input_file)[0])
        log.info("Preparing {0} -> {1}".format(input_file, output_file))

        dat=LoadPickles(input_file)
        header=dat['header']
        vf=dat['vec_feat']
        sf=dat['sca_feat']

        filter=self.Filter(vf, sf)
        for key in sf.keys():
            sf[key]=sf[key][filter]
        for key in vf.keys():
            vf[key]=vf[key][filter, :]
        log.info('{0}/{1} objects selected.'.format(sum(filter), len(filter)))

        # repair the sky lines
        vf['SPECTRA']=base.RemoveSkyLines(vf['SPECTRA'], header)

        # get the emissin lines 
        emission_lines=base.GetEmissionLines(header, vf['SPECTRA'].shape[1])

        # this is the data a algorithm will receive in all
        data={'header': header,
              'vec_feat': vf, 
              'sca_feat': sf,
              'lines': emission_lines}
        SavePickles(output_file, [data])

        return 1
