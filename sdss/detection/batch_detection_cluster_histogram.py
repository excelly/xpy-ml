from ex import *
from ex.pp.common import *

poolsize=2

features=['SpectrumS1', 'ContinuumS1']#, 'Continuum', 'Spectrum']

def DoTask(f):

    dist_threshes=[1, 3]

    for dist_thresh in dist_threshes:
        cmd="python ~/h/python/sdss/detection_clusters_histogram.py --edgefile=spatial/edges_[xyz].pkl --quantfile=quantization/quantization_[{0}][0.5][03][20].pkl --dist_thresh={1} --size_thresh=10 --poolsize=1".format(f, dist_thresh)
        os.system(cmd)

if __name__=='__main__':

    ProcJobs(DoTask, features, poolsize)
