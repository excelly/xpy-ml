import sys
import os

from ex.common import *

InitLog()

poolsize=4

features=[('Continuum', 'Continuum'),
          ('Continuum', 'Raw'),
          ('NonLines', 'NonLines'),
          ('Separated', 'Separated')
          ]
normalizers=['none', 's1']
method=['dist_out', 'energy_out', 'accum_err']
energies=['0.99']

for fs in features:
    for ner in normalizers:
        for m in method:
            for e in energies:
                cmd="python ~/h/python/sdss/global_detection_pca.py --input=./repaired/*.pkl --output=./score --pca_feature={0} --det_feature={1} --normalizer={2} --method={3} --poolsize={5} --pca_energy={4}".format(fs[0], fs[1], ner, m, e, poolsize)
                os.system(cmd)
