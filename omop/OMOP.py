import sys
import os
import shutil as sh
import sqlite3 as sql

import numpy as np
import scipy.io as sio

import ex.util as eu
import base

class OMOP:
    '''class in charge of dealing with the OMOP data set

    the data are managed by folder
    '''

    def __init__(self, modifier, folder):
        '''modifier: the modifier of the data set
        folder: the folder of this data set
        '''

        if folder != '' and not folder.endswith("/"): 
            folder += "/"

        if modifier != '' and not modifier.startswith("_"):
            modifier = "_" + modifier

        self.modifier=modifier
        self.folder=folder

    def GetName(self, t="", name=""):
        return base.GetName(self.modifier, t, name, self.folder)

    def GetDB(self, name=''):
        '''set up the parameters of a db connection
        name: name of the db.
        '''

        name=name.upper()
        eu.check(name in ['', base.join_table_name, base.cond_table_name],
                 'unknown db')

        db=base.GetDB(self.modifier, name, self.folder)
        return db

    def GetUniqueDrugs(self):
        '''get unique drug ids and their counts from db
        '''

        db=self.GetDB()
        r=base.GetUniqueDrugs(db, self.modifier, self.folder)
        db.close()

        return r

    def GetUniqueConds(self):
        '''get unique cond id from db
        '''

        db=self.GetDB()
        r=base.GetUniqueConds(db, self.modifier, self.folder)
        db.close()

        return r

    def GetCTable(self):
        '''get unique cond id from db
        '''

        db=self.GetDB()
        db_cooc=self.GetDB('cooc')

        r=GetCTable(db, db_cooc, self.modifier, self.folder)

        db.close()
        db_cooc.close()
        
        return r

    def GetTrueRelations(self):
        '''get the true relationship list from db
        '''

        db=self.GetDB()
        r=base.GetTrueRelations(db, self.modifier, self.folder)
        db.close()

        return r

    def CreateDB(self, splitter='\t'):
        '''create a database from OMOP data files
        '''

        db=self.GetDB()
        base.CreateDB(db, self.modifier, self.folder, splitter)
        db.close()

    def OrderDB(self):

        db=self.GetDB()
        result_db=base.OrderDB(db, self.modifier, self.folder)
        db.close()

        src_db=self.GetName("db")
        sh.move(src_db, src_db + ".bak")
        sh.move(result_db, src_db)

    def IndexDB(self):
        
        db=self.GetDB()
        base.IndexDB(db)
        db.close()

    def JoinDrugCond(self, date_thresh=30, simu=False):
        '''join the drug exposure and condition occurrence
        '''

        db=self.GetDB()
        base.JoinDrugCond(db, self.modifier, date_thresh, self.folder, simu)
        db.close()

    def ExpandCondOccur(self, simu=False):
        '''expand the condition occurrence table to inject more info
        '''

        db=self.GetDB()
        base.ExpandCondOccur(db, self.modifier, self.folder, simu)
        db.close()

    def GenCountTable(self, thresh_resp=[0], thresh_last=[0,7,14]):
        '''generate the contigency table
        '''

        db=self.GetDB()
        db_cooc=self.GetDB('cooc')
        base.GenCountTable(db, db_cooc, self.modifier, 
                           thresh_resp, thresh_last, self.folder)
        db.close()
        db_cooc.close()
