from ex.pp import *

nproc=1

features=['Spectrum', 'SpectrumS1', 'Continuum', 'ContinuumS1']
# scorers=['pca:rec_err:0.98', 
#          'pca:accum_err:0.98',
#          'pca:dist:0.98',
#          'pca:dist_out:0.98',
#          'pca:accum_dist_out:0.98',
#          'knn:mean_dist:10',
#          'knn:max_dist:10',
#          'mmf:e_svd:5',
#          'mmf:e_nmf:5',
#          'mmf:r_svd:5',
#          'mmf:r_nmf:5']
scorers=['pca:dist:0.98',
         'pca:dist_out:0.98',
         'pca:accum_dist_out:0.98']

def Task(cmd):
    print cmd;
    os.system(cmd)

if __name__ == '__main__':

    jobs = []
    for f in features:
        for m in scorers:
            cmd="python ~/h/python/sdss/detection_point.py --feature={0} --scorer={1} --nproc=1".format(f, m)
            jobs.append(cmd)

    log.info('Batching {0} jobs using {1} processes'.format(len(jobs), nproc))

    ProcJobs(Task, jobs, nproc)
