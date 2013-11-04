import sys
import os
import logging as log
import numpy as np
import scipy.io as sio

from ex.common import *
from ex.io.common import *
import ex.pp.mr as mr
import ex.ml.alg as ml
from ex.plott import *

import base
import sdss_info as sinfo

InitLog()

class Reducer(mr.BaseReducer):
    '''Do PCA on the prepared data.
    '''

    def __init__(self, name, output_type, output_dest):
        mr.BaseReducer.__init__(self, name, output_type, output_dest)

        self.energy_thresh=0.95

    def Reduce(self, params):
        key, input_file=params

        log.info("Gathering info for {0}: {1}".format(key, input_file))

        data=LoadPickles(input_file)
        spectra=data['vec_feat']['SPECTRA']
#        cont=data['vec_feat']['CONTINUUM']
        mask=data['vec_feat']['MASK']
        bady=(mask & sinfo.bad_mask) > 0
        n, dim=spectra.shape

        # filling in default values for bad pixels
        for i in range(n):
            spectra[i,bady[i,:]]=spectra[i,~bady[i,:]].mean()
 #           cont[i,bady[i,:]]=cont[i,~bady[i,:]].mean()

        # for sanity check
        # figure()
        # for i in range(n):
        #     cla()
        #     plot(np.arange(dim), spectra[i,:], 'b', np.arange(dim), cont[i,:], 'r')
        #     draw()
        #     pause()

        return (n, spectra.sum(0), mul(spectra.T, spectra))
        
    def reduce(self, key, results):
        '''combine multiple results of Reduce(). needed for handling
        distributed reducing.
        '''
        
        # aggregate the statistics
        log.debug('Combining immediate results...')
        n, sp_sum, sp_cp=tuple(reduce(lambda d1, d2: [d1[i]+d2[i] for i in range(len(d1))], results))

        sp_mean=vec(sp_sum/n)
        sp_cov=sp_cp/n - mul(sp_mean, sp_mean.T)
#        cont_mean=vec(cont_sum/n)
#        cont_cov=cont_cp/n - mul(cont_mean, cont_mean.T)

        sp_U, sp_L, sp_M, sp_R=ml.pca((sp_mean, sp_cov), self.energy_thresh)
#        cont_U, cont_L, cont_M, cont_R=ml.pca((cont_mean, cont_cov), self.energy_thresh)

        # for sanity check
        # fig=figure()
        # subplot(fig, 121); plot(np.log(sp_L)); title('log(sp L)')
        # subplot(fig, 122); plot(sp_M); title('sp Mean')
        # subplot(fig, 223); plot(np.log(cont_L)); title('log(cont L)')
        # subplot(fig, 224); plot(cont_M); title('cont Mean')
        # pause()

        return {'U': sp_U, 'L': sp_L, 'M': sp_M, 'R': sp_R}
        
    def Save(self, result, path):
        if self.output_type == '.mat':
            sio.savemat(path, result, do_compression=True, oned_as='column')
            # SavePickles(path, [result])
        else:
            raise ValueError('unsupported output format')

class Mapper(mr.BaseMapper):

    def __init__(self, name, output_type, output_dest, pca_models):
        mr.BaseMapper.__init__(self, name, output_type, output_dest)

        self.pca_models=pca_models

    def Smooth(self, pca_model, feature):
        '''smooth samples using pca's major components
        '''

        M=vec(pca_model['M'])
        R=pca_model['R']
        U=pca_model['U'][:, 0:R]

        log.debug('Smoothing the features using PCA with dim={0}'.format(R))
        proj=mul(U.T, shift(feature.T, -M))
        r=shift(mul(U, proj), M).T

        return r

    def Map(self, input_file):
        check(self.output_type == 'file', 'unsupported output type')

        output_file="{0}/{1}.pkl".format(
            self.output_dest, SplitFilename(input_file)[0])
        log.info("Repairing {0} -> {1}".format(input_file, output_file))

        data=LoadPickles(input_file)
        
        spectra=data['vec_feat']['SPECTRA']
#        cont=data['vec_feat']['CONTINUUM']
        mask=data['vec_feat']['MASK']
        bady=(mask & sinfo.bad_mask) > 0
        
        rec=self.Smooth(self.pca_models, spectra)
        rec[~bady]=spectra[~bady]
        data['vec_feat']['SPECTRA']=rec

        # for sanity check
        # n, dim=spectra.shape
        # fig=figure()
        # for i in range(n):
        #     cla()
        #     plot(np.arange(dim), spectra[i,:], 'b', np.arange(dim), rec[i,:], 'r' )
        #     draw()
        #     pause()

#        rec=self.Smooth(self.pca_models['cont_pca'], cont)
#        rec[~bady]=cont[~bady]
#        data['vec_feat']['CONTINUUM']=rec

        SavePickles(output_file, [data])

        return 1

def usage():
    print('''
get the pca model from a prepared sdss data set.

python --input=input_files(wildcard) [--output={output directory}] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

if __name__ == '__main__':
    try:
        opts=getopt(sys.argv[1:], ['output=','input=', 'poolsize=', 'help'])
    except:
        usage()
    if opts.has_key('--help'): usage()

    output_dir=os.path.abspath(opts.get('--output', os.getcwd()))
    input_files=ExpandWildcard(opts['--input'])
    poolsize=opts.get('--poolsize', None)

    reducer=Reducer('PCA_REPAIR', '.mat', output_dir)
    engine=mr.ReduceEngine(reducer, poolsize)

    jobs=input_files
    key='main'
    engine.Start([(key, jobs)])

    pca_model_file=engine.OutFilename(key)
    pca_model=sio.loadmat(pca_model_file, struct_as_record=True)

    mapper=Mapper('PCA_REPAIR', 'file', output_dir, pca_model)
    engine=mr.MapEngine(mapper, poolsize)
    engine.Start(jobs)
