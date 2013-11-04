from ex.common import *
from common import *
from FITS import FITS
import ex.pp.mr as mr

class Reducer(mr.BaseReducer):
    '''convert FITS files into Matlab files
    '''

    def __init__(self, output_dest):
        mr.BaseReducer.__init__(self, "FITS2Mat Reducer", True)
        self.output_dest=output_dest

    def GetKey(self, filename):
        return filename

    def Reduce(self, key, vals):
        input_file=vals[0]
        output_file="{0}/{1}.mat".format(self.output_dest, 
                                         SplitFilename(input_file)[0])
        log.info("Converting {0} -> {1}".format(input_file, output_file))

        FITS(input_file).SaveAsMat(output_file)

        return 1

    def Aggregate(self, results):
        keys, points=unzip(results)
        return sum(points)
