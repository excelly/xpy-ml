import sys
import os
import logging as log

import numpy as np

from ex.common import *
from ex.io.common import *
import ex.pp.mr as mr
import ex.array as ea
import sdss_info as sinfo
import base

class Mapper(mr.BaseMapper):
    '''compact the data. input files should be grouped to reduce the
    size of inmmediate reducer results.
    '''

    def Map(self, input_files):
        if not isinstance(input_files, list): input_files=[input_files]
        check(self.output_type == 'file', 'unsupported output type')

        n_files=len(input_files)
        input_file=input_files[0]
        output_file="{0}/{1}_group.pkl".format(
            self.output_dest, SplitFilename(input_file)[0])

        # if the file has already been processed
        if os.path.exists(output_file): 
            log.info('Skipping group {0}'.format(output_file))
            return n_files

        log.info("Processing {0} files (group of '{1}') -> {2}".format(
                n_files, input_file, output_file))

        vector_feat=[]
        scalar_feat=[]
        for input_file in input_files:
            fid=SplitFilename(input_file)[0]
            hdus=LoadPickles(input_file)['hdus']

            header=hdus[0]['header']

            sf=hdus[1]['data']
            sf=dict(sf, **hdus[1]['spec_data'])

            vf={'SPECTRA': hdus[0]['data'],
                'CONTINUUM': sf.pop('CONTINUUM'),
                'NOISE': sf.pop('NOISE'),
                'MASK': sf.pop('MASK')}
            vf=dict(vf, **hdus[1]['line_data'])

            vector_feat.append(vf)
            scalar_feat.append(sf)
            
        data_v={}
        for key in vector_feat[0].keys():
            data_v[key]=ea.AssembleMatrix(vector_feat, key, True)
        data_s={}
        for key in scalar_feat[0].keys():
            data_s[key]=ea.AssembleVector(scalar_feat, key)

        SavePickles(output_file, [{'header': header, 
                                   'vec_feat': data_v, 
                                   'sca_feat': data_s}])

        return n_files
