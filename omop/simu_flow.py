import sys
import os
import shutil as sh
import logging as log
import multiprocessing as mp

import ex.util as eu
from OMOP import OMOP
import base

eu.InitLog(log.INFO)

dat_dest="D:/Documents/DataSet/omop/simulation/"
# dat_dest="~/h/data/omop/simulation/"

def DoTask(configs):
    modifier=configs[0]

    folder=base.Simulate(
        modifier, validation=True, n_drug=10, n_cond=10, n_person=500, 
        cond_alt=configs[1], ob_alt=configs[2], drug_alt=configs[3], 
        dexposure_alt=configs[4],doutcome_alt=configs[5],ind_alt=configs[6],
        no_simu=True)

    ds=OMOP(modifier, folder)
    ds.CreateDB()
    ds.OrderDB()
    ds.IndexDB()
    ds.JoinDrugCond(simu=True)
    ds.ExpandCondOccur(simu=True)
    ds.GenCountTable()

    return(folder)

if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1].startswith('s'):
        log.info('''OMOP Single threaded simulation.''')
        parallel=False
    else:
        log.info('''OMOP Parallel simulation.''')
        parallel=True

        log.warn("A Numpy bug may make char arrays wrong in matlab. To fix A, use A=reshape(A, size(A,2), size(A,1))'")

    tasks=[# ("TEST", False, False, False, False, False, False),
           # ("TEST_C", True, False, False, False, False, False),
           # ("TEST_OB", False, True, False, False, False, False),
           # ("TEST_D", False, False, True, False, False, False),
           # ("TEST_DE", False, False, False, True, False, False),
           # ("TEST_DO", False, False, False, False, True, False),
           # ("TEST_IN", False, False, False, False, False, True),
           ("TEST_C_D_DO", True, False, True, False, True, False),
           ("TEST_D_DO", False, False, True, False, True, False),
           ]

    if parallel:
        pool_size=min((mp.cpu_count() - 1, len(tasks), 5))
        p=mp.Pool(max(2,pool_size))
        folders=p.map(DoTask, tasks)
    else:
        folders=[DoTask(task) for task in tasks]

    for folder in folders:
        os.system("mv {0}/*.mat {1}".format(folder, dat_dest))
        os.system("cp {0}/*.db3 {1}".format(folder, dat_dest))
