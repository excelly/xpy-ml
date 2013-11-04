from ex import *

nproc = 15

features=['SpectrumS1', 'ContinuumS1', 'Continuum','Spectrum']
cluster_files = ['spatial_clusters_[xyz][10][1].pkl', 
                 'spatial_clusters_[xyz][10][3].pkl', 
                 'spatial_clusters_[xyz][10][5].pkl']
size_ranges=['10-30', '30-50', '10-100']
model_penalty = [1, 5]

if __name__=='__main__':

    for sr in size_ranges:
        for f in features:
            for cf in cluster_files:
                for pen in model_penalty:
                    cmd = 'python ~/h/python/sdss/detection_clusters_bagmodel.py --feature_names={0} --cluster_file={1} --size_range={2} --nproc={3} --model_penalty={4}'.format(f, cf, sr, nproc, pen)
                    print "Executing the command:\n", cmd
                    os.system(cmd)
