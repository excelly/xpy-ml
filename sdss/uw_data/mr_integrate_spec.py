import sys
import os
import logging as log

import numpy as np

from ex.common import *
from ex.io.common import *
import ex.pp.mr as mr
import ex.array as ea
import base

class Mapper(mr.BaseMapper):
    '''take the raw expanded sdss data and integrate them into useful
    data files.  '''

    def Map(self, input_file):
        check(not isinstance(input_file, list), 
                 'this converter does not support grouping files')
        check(self.output_type == 'file', 'unsupported output type')

        filename=SplitFilename(input_file)[0]
        output_file="{0}/{1}.pkl.bz".format(self.output_dest, filename)

        # if the file has already been processed
        if os.path.exists(output_file): 
            log.info('Skipping {0}'.format(input_file))
            return 1

        log.info("Processing {0} -> {1}".format(input_file, output_file))

        dat=LoadPickles(input_file)

        hdus=dat['hdus']
        header=hdus[0]['header']
        n, dim=hdus[0]['data'].shape

        # extract info in the primary HDU
        spec_header_primary=[sp[0]['header'] for sp in dat['spec']]
        interesting_things=['Z_STATUS', 'Z_WARNIN', 'RAOBJ', 'DECOBJ',
                            'SN_I', 'SN_R', 'SN_G', 'NGOOD']
        hdus[1]['spec_data']={}
        for t in interesting_things:
            hdus[1]['spec_data'][t]=ea.AssembleVector(spec_header_primary, t)

        # extract spectra-related info
        specs=dat['spec']
        spectrum=np.zeros((n, dim), dtype=specs[0][0]['data'].dtype)
        continuum=np.zeros((n, dim), dtype=spectrum.dtype)
        noise=np.zeros((n, dim), dtype=spectrum.dtype)
        mask=np.zeros((n, dim), dtype=np.int32)
        for i in range(n):
            spectrum[i,:], continuum[i,:], noise[i,:], mask[i,:]=base.ReBin(
                specs[i][0]['data'], specs[i][0]['header'], header)

        # hdus[1]['data']['SPECTRUM']=spectrum
        hdus[1]['spec_data']['CONTINUUM']=continuum
        hdus[1]['spec_data']['NOISE']=noise
        hdus[1]['spec_data']['MASK']=mask

        # extract line info from HDU 2
        hdus[1]['line_data']={}
        spec_data_line=[sp[2]['data'] for sp in dat['spec']]
        interesting_things=['wave', 'waveErr', 'waveMin', 'waveMax',
                            'height', 'continuum', 'chisq']
        for t in interesting_things:
            # sometimes xxxx happens
            for k in range(n):
                d=spec_data_line[k][t]
                if len(d) < 44:
                    tmp=-99999.0*np.ones(44, dtype=d.dtype)
                    tmp[0:d.size]=d
                    spec_data_line[k][t] = tmp

            vec=ea.AssembleVector(spec_data_line, t)
            hdus[1]['line_data'][t]=vec.reshape((n, len(spec_data_line[0][t])))
    
        SavePickles(output_file, [{'hdus': hdus}])

        return 1
