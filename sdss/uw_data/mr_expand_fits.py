import sys
import os
import logging as log
import urllib
import socket
socket.setdefaulttimeout(30)

import numpy as np

from ex.common import *
from ex.io.common import *
from ex.io.FITS import FITS
import ex.pp.mr as mr
import base

class Mapper(mr.BaseMapper):
    '''download spec files from the sdss website to expand the data we
    have from UW.
    '''

    def GetSpecURL(self, target):
        return target.replace('/astro/net/scratch1/sdssspec', 'http://das.sdss.org')

    def Map(self, input_file):
        check(not isinstance(input_file, list), 
                 'this converter does not support grouping files')
        check(self.output_type == 'file', 'unsupported output type')

        filename=SplitFilename(input_file)[0]
        output_file="{0}/{1}.pkl.bz".format(self.output_dest, filename)
        tmp_dir=self.output_spec[1] if os.name == 'nt' else '/dev/shm'

        # if the file has already been processed
        if os.path.exists(output_file): 
            log.info('Skipping {0}'.format(input_file))
            return 1

        # read the dat file
        fits=FITS(input_file)
        hdus=fits.HDUs
        targets=hdus[1].data.TARGET
        spec_urls=[self.GetSpecURL(target) for target in targets]
        ids=[target[58:-4] for target in targets]
        plate=ids[0].split('-')[1]

        spec_info=[]
        for ind in range(len(spec_urls)): # process each object
            spec_url=spec_urls[ind]
            tmp_spec_file='{0}/{1}.fits'.format(tmp_dir, ids[ind])

            # download the original spec
            try:
                urllib.urlretrieve(spec_url, tmp_spec_file)
            except Exception as ex:
                log.warn("Download of {0} failed. Try again later.\nError: {1}".format(plate, ex))
                return 0
            log.debug('Downloaded {0}.'.format(spec_url))

            # read the original spec
            spec=FITS(tmp_spec_file)
            try: 
                spec.HDUs[0].verify('fix')
            except: 
                log.warning('Object {0} cannot be fixed. Skipping this plate.'.format(ids[ind]))
                return 0

            # extract the info
            spec_info.append(spec.GetMats())

            # clean up
            spec.Close()
            os.remove(tmp_spec_file)

        log.debug('Saving to {0}...'.format(output_file))
        SavePickles(output_file, [{"hdus":fits.GetMats(), "spec":spec_info}])
        log.info("Plate {0} ({1} objects) processed.".format(plate, len(ids)))
        
        return 1
