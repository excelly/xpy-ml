from ex.common import *
from common import *
import ex.pp.mr as mr

class Reducer(mr.BaseReducer):
    '''convert a pickle file into a Matlab data file.  the pickle
    should contain just one dict that is acceptable for
    scipy.io.savemat().
    '''

    def __init__(self, output_dest):
        mr.BaseReducer.__init__(self, "Pickle2Mat", True)
        self.output_dest=output_dest

    def GetKey(self, filename):
        return filename

    def Reduce(self, key, vals):
        input_file=vals[0]
        output_file="{0}/{1}.mat".format(self.output_dest, 
                                         SplitFilename(input_file)[0])
        log.info("Converting {0} -> {1}".format(input_file, output_file))

        dat=LoadPickles(input_file)
        for key in dat.keys():
            item=dat[key]
            if isinstance(item, list) or isinstance(item, tuple):
                dat[key]=np.array(item, dtype=np.object)

        SaveMat(output_file, dat)

        return 1

    def Aggregate(self, results):
        keys, points=unzip(results)
        return sum(points)
