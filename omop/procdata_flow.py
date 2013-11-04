import os
import shutil as sh
import logging as log

import ex.util as eu
from OMOP import OMOP

eu.InitLog(log.DEBUG)

modifier=""
folder="OSIM/"
 
dat_dest="/opt/lxiong/omop/c1/data"

ds=OMOP(modifier, folder)
#ds.CreateDB()
#ds.OrderDB()
#ds.IndexDB()
#ds.ExpandCondOccur(simu=False)
ds.JoinDrugCond(simu=False)
# ds.GenCountTable()

#os.system("mv {0}/*.mat {1}".format(folder, mat_dest))
