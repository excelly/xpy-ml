import os
import sys
import time
from datetime import datetime
import shutil as sh
import logging as log
import sqlite3 as sql

import numpy as np
import scipy as sp
import scipy.io as sio

import ex.array as ea
from ex.io.common import *

import simu_config as config

table_files=["PERSON",
             "OBSERVATION_PERIOD",
             "DRUG_EXPOSURE",
             "CONDITION_OCCURRENCE",
             "TRUE_RELATIONSHIPS",
             "DRUG_OUTCOMES"]

join_table_name="COOC"
cond_table_name="COND"
ctable_name="cooc_table"
truth_name="true_rel"
drug_uid_name="drug_uid"
cond_uid_name="cond_uid"

def Date2Num(str, format="%Y-%m-%d"):
    '''convert a date string to double
    '''

    if len(str) == 0: return(-1)
    else: return(time.mktime(datetime.strptime(str,format).timetuple()))

def GetName(modifier, t="", name="", folder=""):
    '''get the name of entities

    t: type of the entity
    folder: folder of the data set
    '''

    if t == "db":
        if len(name) > 0 and not name.startswith("_"): name = "_" + name
        return("{0}OSIM{1}{2}.db3".format(folder, modifier, name))
    elif t == "table":
        filename="{0}OSIM_{1}{2}".format(folder, name, modifier)
        if table_files.index(name) < 4 and modifier != "": 
            filename += "_1"
        return(filename + ".txt")
    else:
        return("{0}{1}{2}".format(folder, name, modifier))

def GetDB(modifier, name="", folder=""):
    '''set up the parameters of a db connection
    '''

    db_name=GetName(modifier, "db", name=name, folder=folder)
    log.debug("Openning DB {0}".format(db_name))

    db=sql.connect(db_name)
    db.execute("pragma cache_size=2000000")

    return(db)

def GetUniqueDrugs(db, modifier, folder=""):
    '''get unique drug ids and their counts from db
    '''
    
    name=drug_uid_name
    filename=GetName(modifier, "", name, folder) + ".mat"
    log.debug("File for unique drug ID: {0}".format(filename))

    if os.path.exists(filename):
        log.debug("Reading off-the-shelf drug ID")
        d=sio.loadmat(filename, struct_as_record=True)
        return d[name].ravel()
    else:
        log.debug("Collecting unique drug ID and counts...")
        cur=db.execute('''select distinct DRUG_CONCEPT_ID
from 
    DRUG_EXPOSURE_Drug''')
        uid=[r[0] for r in cur]

        if len(uid) > 0:
            uid=np.array(uid, dtype=np.int32)
            log.debug("{0} unique drug ID found.".format(uid.size))
        else:
            uid=np.zeros(0)
            log.debug("No drug found")

        sio.savemat(filename, {name:uid}, do_compression=True, oned_as='column')

        return uid.ravel()

def GetUniqueConds(db, modifier, folder=""):
    '''get unique cond id from db
    '''

    name=cond_uid_name
    filename=GetName(modifier, "", name, folder) + ".mat"
    log.debug("File for unique cond ID: {0}".format(filename))

    if os.path.exists(filename):
        log.debug("Reading off-the-shelf cond ID")
        d=sio.loadmat(filename, struct_as_record=True)
        return d[name].ravel()
    else:
        log.debug("Collecting unique cond ID and counts...")
        cur=db.execute('''select distinct CONDITION_CONCEPT_ID
from 
    CONDITION_OCCURRENCE_Cond''')
        uid=[r[0] for r in cur]

        if len(uid) > 0:
            uid=np.array(uid, dtype=np.int32)
            log.debug("{0} cond ID found.".format(uid.size))
        else:
            uid=np.zeros(0)
            log.debug("No cond found")

        sio.savemat(filename, {name:uid}, do_compression=True, oned_as='column')

        return uid.ravel()

def GetTrueRelations(db, modifier, folder=""):
    '''get the true relationship list from db
    '''

    name=truth_name
    filename=GetName(modifier, "", name, folder) + ".mat";
    log.debug("File for true associations: {0}".format(filename))

    if os.path.exists(filename):
        log.debug("Reading off-the-shelf true relationships")
        d=sio.loadmat(filename, struct_as_record=True)
        return(d[name])
    else:
        log.debug("Collecting true relationships...")
        d=db.execute('''select DRUG_ID, CONDITION_ID, ASSOCIATION_PRESENT
from TRUE_RELATIONSHIPS''').fetchall()

        d=np.array(d, dtype=np.int32)
        log.debug("{0} true relationships found.".format(d.shape[0]))

        sio.savemat(filename, {name:d}, 
                    do_compression=True, oned_as='column')
        return(d)

def GenCmd(table, fields):
    '''generate the create and insert statement for the database'''
    
    arg_list=[]
    for field in fields:
        if field.endswith("_ID"): 
            type="INTEGER"
        elif field.endswith("_DATE"): 
            type="REAL"
        elif field.startswith("YEAR_"): 
            type="INTEGER"
        elif field in ("ASSOCIATION_PRESENT", "A_TYPE"): 
            type="INTEGER"
        else: type="TEXT"
        
        arg_list.append("{0} {1}".format(field, type))
        
    create_cmd="CREATE TABLE {0} ({1})".format(
        table, ','.join(arg_list))
    
    insert_cmd="INSERT INTO {0} VALUES ({1})".format(
        table, ','.join(['?']*len(fields)))

    return((create_cmd, insert_cmd))

def GenGroundTruth(outcome_file, truth_file, splitter="\t"):
    '''generate the truth file from outcome file
    '''

    log.info("Generating groundtruth to {0}".format(truth_file))

    true_ass={}
    with xFile(outcome_file) as input:
        line=input.readline().strip()
        header=line.split(splitter)
        ncol=len(header)

        drug_col=header.index("DRUG_ID")
        cond_col=header.index("CONDITION_ID")
        risk_col=header.index("DRUG_OUTCOME_ATTRIB_RISK_CATEGORY")
        
        for line in input:
            line=line.replace('\n','').split(splitter)
            line=[line[i] for i in [drug_col, cond_col, risk_col]]
            
            if line[2].startswith("Small"): 
                true_ass[(int(line[0]),int(line[1]))]=1
            elif line[2].startswith("Moderate"): 
                true_ass[(int(line[0]),int(line[1]))]=2
            elif line[2].startswith("Large"): 
                true_ass[(int(line[0]),int(line[1]))]=3

    with xFile(truth_file, "w") as output:
        output.write("{0}\t{1}\t{2}\n".format(
                "DRUG_ID","CONDITION_ID","ASSOCIATION_PRESENT"))
        for key in true_ass.keys():
            output.write("{0}\t{1}\t{2}\n".format(
                    key[0], key[1], true_ass[key]))

    log.info("{0} pairs found".format(len(true_ass.keys())))

def ImportTable(db, table, file_name, splitter="\t"):
    '''import a table file into the database
    '''

    log.info("Importing table {0} from {1}".format(table, file_name))

    d=db.execute("select * from sqlite_master where type='table' and name='{0}'".format(table)).fetchall()
    if len(d) > 0:
        log.warn("Table {0} exists. Skipping.".format(table))
        return

    cur=db.cursor()
    with xFile(file_name) as input:
        line=input.readline().strip()
        header=line.split(splitter)
        log.debug("Table {0} has columns {1}".format(table, header))
        ncol=len(header)

        # generate the commands
        create_cmd, insert_cmd=GenCmd(table, header)
        log.debug("CMD: \n** {0}\n** {1}".format(create_cmd, insert_cmd))

        # create the table
        cur.execute(create_cmd)
        db.commit()
        
        # insert the data
        while True:
            lines=input.readlines(int(1e7))
            if len(lines) == 0: break

            entries=[l.replace('\n','').split(splitter) for l in lines]

            entries=zip(*entries)
            for ind in range(len(header)):
                if header[ind].endswith("_DATE"):
                    entries[ind]=[Date2Num(s) for s in entries[ind]]
            entries=zip(*entries)

            cur.executemany(insert_cmd, entries)
        db.commit()

def OrderDB(db, modifier, folder="", output_file=None):
    '''order the tables of the DB
    '''

    key="PERSON_ID"

    if output_file is None:
        output_file=GetName(modifier, "db", "SORTED", folder)

    db.execute("attach '{0}' as o".format(output_file))
    
    log.info("Sorting PERSON with {0}...".format(key))
    db.execute("create table o.PERSON as select * from PERSON order by {0}".format(key));

    log.info("Sorting OP with {0}...".format(key))
    db.execute("create table o.OBSERVATION_PERIOD as select * from OBSERVATION_PERIOD order by {0}".format(key));

    log.info("Sorting DE with {0}...".format(key))
    db.execute("create table o.DRUG_EXPOSURE as select * from DRUG_EXPOSURE order by {0}".format(key));

    key="DRUG_CONCEPT_ID"
    log.info("Sorting DED with {0}...".format(key))
    db.execute("create table o.DRUG_EXPOSURE_Drug as select * from DRUG_EXPOSURE order by {0}".format(key));

    key="PERSON_ID"
    log.info("Sorting CC with {0}...".format(key))
    db.execute("create table o.CONDITION_OCCURRENCE as select * from CONDITION_OCCURRENCE order by {0}".format(key));

    key="CONDITION_CONCEPT_ID"
    log.info("Sorting CCC with {0}...".format(key))
    db.execute("create table o.CONDITION_OCCURRENCE_Cond as select * from CONDITION_OCCURRENCE order by {0}".format(key));

    key="DRUG_ID"
    log.info("Sorting Truth with {0}...".format(key))
    db.execute("create table o.TRUE_RELATIONSHIPS as select * from TRUE_RELATIONSHIPS order by {0}".format(key));

    db.execute("detach o")

    return output_file

def IndexDB(db):
    '''index the columns in the db
    '''

    # PERSON
    log.info("Indexing IDX_PERSON_PERSON_ID")
    db.execute("create index if not exists IDX_PERSON_PERSON_ID on PERSON (PERSON_ID)")

    # OBSERVATION_PERIOD
    log.info("Indexing IDX_OP_PERSON_ID")
    db.execute("create index if not exists IDX_OP_PERSON_ID on OBSERVATION_PERIOD (PERSON_ID)")

    # DRUG_EXPOSURE
    log.info("Indexing IDX_DE_PERSON_ID")
    db.execute("create index if not exists IDX_DE_PERSON_ID on DRUG_EXPOSURE (PERSON_ID)")
    log.info("Indexing IDX_DE_START_DATE")
    db.execute("create index if not exists IDX_DE_START_DATE on DRUG_EXPOSURE (DRUG_EXPOSURE_START_DATE)")
    log.info("Indexing IDX_DE_END_DATE")
    db.execute("create index if not exists IDX_DE_END_DATE on DRUG_EXPOSURE (DRUG_EXPOSURE_END_DATE)")
    log.info("Indexing IDX_DED_DRUG_ID")
    db.execute("create index if not exists IDX_DED_DRUG_ID on DRUG_EXPOSURE_Drug (DRUG_CONCEPT_ID)")

    # CONDITION_OCCURRENCE
    log.info("Indexing IDX_CC_PERSON_ID")
    db.execute("create index if not exists IDX_CC_PERSON_ID on CONDITION_OCCURRENCE (PERSON_ID)")
    log.info("Indexing IDX_CC_START_DATE")
    db.execute("create index if not exists IDX_CC_START_DATE on CONDITION_OCCURRENCE (CONDITION_START_DATE)")
    log.info("Indexing IDX_CCC_CONDITION_ID")
    db.execute("create index if not exists IDX_CCC_CONDITION_ID on CONDITION_OCCURRENCE_Cond (CONDITION_CONCEPT_ID)")

def CreateDB(db, modifier, folder="", splitter='\t'):
    '''create a database from OMOP data files
    '''

    # handling groundtruth
    outcome_file=GetName(modifier, "table", table_files[-1], folder)
    log.debug("Using groundtruth file {0}".format(outcome_file))
    if os.path.exists(outcome_file):
        truth_file=GetName(modifier, "table", table_files[-2], folder)
        GenGroundTruth(outcome_file, truth_file)

    # handling observations
    for tid in range(len(table_files) - 1):
        table=table_files[tid]
        file_name=GetName(modifier, "table", table, folder)
        ImportTable(db, table, file_name)

def ExpandCondOccur(db, modifier, folder="", simu=False):
    '''expand the condition occurrence table to inject more info
    '''

    log.info("Expanding condition occurrences {0}".format(
            "for simulation" if simu else ""))

    db.execute("attach '{0}' as db_out".format(
            GetName(modifier, "db", name=cond_table_name, folder=folder)))

    log.info("Expanding {0}...".format(modifier))
    db.create_function("GetAge", 2, GetAge)
    db.execute('''create table db_out.{0} as 
select p.PERSON_ID as PERSON_ID, p.YEAR_OF_BIRTH as YEAR_OF_BIRTH, GetAge(p.YEAR_OF_BIRTH, c.CONDITION_START_DATE) as AGE, p.GENDER_CONCEPT_ID as GENDER_CONCEPT_ID, p.RACE_CONCEPT_ID as RACE_CONCEPT_ID,
c.CONDITION_OCCURRENCE_ID as CONDITION_OCCURRENCE_ID, c.CONDITION_START_DATE as CONDITION_START_DATE, c.CONDITION_CONCEPT_ID as CONDITION_CONCEPT_ID{1}
from 
    PERSON as p cross join 
    CONDITION_OCCURRENCE as c
where
    p.PERSON_ID = c.PERSON_ID
'''.format(cond_table_name,
           ", c.A_TYPE as A_TYPE, " if simu else ""))
    db.commit()
    log.debug("Expansion done")

    nrow=db.execute("select count(CONDITION_OCCURRENCE_ID) from db_out.{0}".format(cond_table_name)).fetchall()
    log.info("Expanded {0}".format(nrow[0][0]))

    db.execute("create index db_out.IDX_{0}_PERSON on {0} (PERSON_ID)".format(cond_table_name))
    db.commit()
    log.info("IDX_PERSON done")

    db.execute('''create table db_out.{0}_Cond as
select * from db_out.{0} order by CONDITION_CONCEPT_ID
'''.format(cond_table_name))
    db.commit()
    log.info("Sorting done.")

    db.execute("create index db_out.IDX_{0}C_COND on {0}_Cond (CONDITION_CONCEPT_ID)".format(cond_table_name))
    db.commit()
    log.info("IDX_CONDITION done")

    if simu:
        db.execute("create index db_out.IDX_{0}C_A_TYPE on {0}_Cond (A_TYPE)".format(cond_table_name))
        db.commit()
        log.info("IDX_A_TYPE done")

def JoinDrugCond(db, modifier, date_thresh=30, folder="", simu=False):
    '''join the drug exposure and condition occurrence
    '''

    log.info("Joining drug exposures and conditions {0}".format(
            "for simulation" if simu else ""))

    db.execute("attach '{0}' as db_out".format(
            GetName(modifier, "db", name=join_table_name, folder=folder)))

    db.execute("attach '{0}' as db_cond".format(
            GetName(modifier, "db", name=cond_table_name, folder=folder)))

    log.info("Joinning {0}...".format(modifier))
    db.execute('''
create table db_out.{0} as 
select d.DRUG_CONCEPT_ID as DRUG_CONCEPT_ID, d.DRUG_EXPOSURE_ID as DRUG_EXPOSURE_ID, d.DRUG_EXPOSURE_START_DATE as DRUG_EXPOSURE_START_DATE, d.DRUG_EXPOSURE_END_DATE as DRUG_EXPOSURE_END_DATE,
c.PERSON_ID as PERSON_ID, c.AGE as AGE, c.GENDER_CONCEPT_ID as GENDER_CONCEPT_ID, c.RACE_CONCEPT_ID as RACE_CONCEPT_ID, 
c.CONDITION_OCCURRENCE_ID as CONDITION_OCCURRENCE_ID, c.CONDITION_START_DATE as CONDITION_START_DATE, c.CONDITION_CONCEPT_ID as CONDITION_CONCEPT_ID{1}
from 
    DRUG_EXPOSURE as d cross join 
    db_cond.COND as c
where
    d.PERSON_ID = c.PERSON_ID and
    d.DRUG_EXPOSURE_START_DATE <= c.CONDITION_START_DATE and
    d.DRUG_EXPOSURE_END_DATE+{2} >= c.CONDITION_START_DATE
'''.format(join_table_name, 
           ", c.A_TYPE as A_TYPE" if simu else "", 
           date_thresh*24*60*60))
    db.commit()

    log.debug("Join done.")
    nrow=db.execute("select count(PERSON_ID) from db_out.COOC").fetchall()
    log.info("Joined {0}".format(nrow[0][0]))

    db.execute('''create table db_out.{0}_Drug as
select * from db_out.{0} order by DRUG_CONCEPT_ID, CONDITION_CONCEPT_ID
'''.format(join_table_name))
    db.commit()
    log.info("Sorting done.")

    idx_cmd="CREATE INDEX db_out.IDX_{0}D_DRUG_COND_TYPE ON {0}_Drug (DRUG_CONCEPT_ID, CONDITION_CONCEPT_ID{1})".format(join_table_name, ", A_TYPE" if simu else "")
    db.execute(idx_cmd)
    db.commit()
    log.info("IDX_{0}D_DRUG_COND done".format(join_table_name))

    idx_cmd="CREATE INDEX db_out.IDX_{0}_PERSON ON {0} (PERSON_ID)".format(join_table_name)
    db.execute(idx_cmd)
    db.commit()
    log.info("IDX_{0}_PERSON done".format(join_table_name))

    db.execute('detach db_out')
    db.execute('detach db_cond')

def GenCountTable(db, db_cooc, modifier, thresh_resp=[0], thresh_last=[0,7,14], folder=""):
    '''generate the basic contigency table
    '''

    log.info("Generating contingency tables for t1={0}, t2={1}".format(
            thresh_resp, thresh_last))

    true_rel=GetTrueRelations(db, modifier, folder)
    drug_uid, drug_count=GetUniqueDrugs(db, modifier, folder)
    cond_uid, cond_count=GetUniqueConds(db, modifier, folder)

    for resp_t in thresh_resp:
        for last_t in thresh_last:
            log.info("Processing t1={0}, t2={1}".format(resp_t, last_t))

            C=np.zeros((drug_uid.size, cond_uid.size))

            cmd='''select DRUG_CONCEPT_ID, CONDITION_CONCEPT_ID
from 
    COOC 
where
    CONDITION_START_DATE >= DRUG_EXPOSURE_START_DATE + {0} and
    CONDITION_START_DATE <= DRUG_EXPOSURE_END_DATE + {1}
'''.format(resp_t*24*3600, last_t*24*3600)

            cur=db_cooc.execute(cmd)
            cur.arraysize=1024
            dat=cur.fetchmany()
            while len(dat) > 0:
                dat=np.array(dat, dtype=np.int32)
                e_drug=EncodeArray(dat[:,0].ravel(), drug_uid)
                e_cond=EncodeArray(dat[:,1].ravel(), cond_uid)
                C=accumarray(np.vstack((e_drug, e_cond)), base=C)

                dat=cur.fetchmany()
            cur.close()

            C_name=GetName(modifier, "", "Count", folder)
            C_name += "_{0}_{1}".format(resp_t, last_t)
            sio.savemat(C_name, {"C":C,
                                 "drug_uid":drug_uid,
                                 "cond_uid":cond_uid,
                                 "drug_count":drug_count,
                                 "cond_count":cond_count,
                                 "true_rel":true_rel}, 
                        do_compression=True, oned_as='column')

def GetCTable(db, db_cooc, modifier, folder=""):
    '''get unique cond id from db
    '''

    name=ctable_name
    filename=GetName(modifier, "", name, folder) + ".mat"
    log.debug("File for contingincy table: {0}".format(filename))

    if os.path.exists(filename):
        log.debug("Reading off-the-shelf cooc-table")
        d=sio.loadmat(filename, struct_as_record=True)
        return d[name]
    else:
        log.debug("Collecting co-table...")
        drug_uid=GetUniqueDrugs(db, modifier, folder=folder)[0]
        n_drug=drug_uid.size
        cond_uid=GetUniqueConds(db, modifier, folder=folder)[0]
        n_cond=cond_uid.size

        ctable=np.zeros((n_drug, n_cond), dtype=np.int32)
        for di in range(n_drug):
            for ci in range(n_cond):
                d=GetCOOCData(db_cooc, drug_uid, cond_uid, 
                              drug_uid[di], cond_uid=[ci])
                ctable[di, ci]=len(d)

        sio.savemat(filename, {name:ctable}, 
                    do_compression=True, oned_as='column')

        return ctable

def Simulate(modifier, n_drug=50, n_cond=50, n_person=10000, 
             start_year=2000, end_year=2002, validation=True, 
             simulator="OSIM_MAIN.R", 
             cond_alt=False, ob_alt=False, drug_alt=False, 
             dexposure_alt=False, doutcome_alt=False, ind_alt=False,
             no_simu=False):

    log.info("Simulating OMOP {4} data with {0} drugs, {1} conditions, {2} persons, {3} years".format(n_drug, n_cond, n_person, end_year - start_year, modifier))

    validation='TRUE' if validation else 'FALSE'

    exec_config_file="tmp_OSIM_{0}_execParms".format(modifier)
    dist_config_file="tmp_OSIM_{0}_distParms".format(modifier)
    wrapper_file="tmp_OSIM_{0}_wrapper.r".format(modifier)
    result_folder='OSIM_{0}'.format(modifier)

    if no_simu: 
        log.info("No actual simulation performed")
        return(result_folder)

    if os.path.exists(result_folder):
        s=raw_input("Result folder already exists. Overwrite? [y/N]")
        if s.lower() == 'y':
            sh.rmtree(result_folder)
        else: 
            log.info("Simulator not executed")
            return("")

    # generate configuration
    exec_config='''simName=Test Patient Set 1
simDescription=test simulation for Auton
personCount={0}
personStartID=1
drugCount={1}
conditionCount={2}
minDatabaseDate={3}
maxDatabaseDate={4}
createSimTables=TRUE
createSimPersons=TRUE
validationMode={5}
fileModifier={6}
fileDistNumber=1
'''.format(n_person, n_drug, n_cond, start_year, end_year, validation, modifier)
    with xFile(exec_config_file + ".txt", "w") as output:
        output.write(exec_config)

    log.info('''Options:
* Condition: {0}
* OB: {1}
* DRUG: {2}
* Exposure: {3}
* Drug Outcome: {4}
* Indication: {5}'''.format(cond_alt, ob_alt, drug_alt, dexposure_alt, doutcome_alt, ind_alt))

    dist_config='\n'.join(
        [config.person_config_default,
         config.drug_config_default if not drug_alt else config.drug_config_alt,
         config.ob_config_default if not ob_alt else config.ob_config_alt,
         config.drug_exposure_config_default if not dexposure_alt else config.drug_exposure_config_alt,
         config.drug_outcome_config_default if not doutcome_alt else config.drug_outcome_config_alt,
         config.ind_config_default if not ind_alt else config.ind_config_alt,
         config.cond_config_default if not cond_alt else config.cond_config_alt
         ])
    with xFile(dist_config_file + ".txt", "w") as output:
        output.write(dist_config)

    wrapper_script='''source('{0}');
OSIM.INPUT.PARMS.FILENAME <- '{1}'; 
OSIM.INPUT.DISTRIBUTION.FILENAME <- '{2}'; 
main();
'''.format(simulator, exec_config_file, dist_config_file)
    with xFile(wrapper_file, "w") as output:
        output.write(wrapper_script)
        
    log.info("Simulating {0}...".format(modifier))
    if os.system('R CMD BATCH ' + wrapper_file) != 0:
        raise RuntimeError("R failed.")
    log.info("Simulation done")

    return(result_folder)

def GetCOOCData(db_cooc, drug_uid, cond_uid, drug_id=None, cond_id=None):
    '''return the co-occurrence data of a drug or a condition or both
    '''

    eu.check(drug_id is not None or cond_id is not None, 
             'must specify the drug or condition')

    if drug_id is not None and cond_id is not None:
        d=db_cooc.execute('''SELECT * from COOC_Drug
WHERE drug_concept_id={0} and condition_concept_id={1}
'''.format(drug_id, cond_id)).fetchall()
    else:
        db_cooc.execute("attach ':memory:' as db_out")

        if cond_id is None: # if to find out all about a drug
            log.debug('Getting COOC data for a drug')

            log.debug('First level selection...')
            db_cooc.execute('''CREATE TABLE db_out.D as
SELECT * from COOC_Drug 
WHERE drug_concept_id={0}'''.format(drug_id))
            
            log.debug('Secondary indexing...')
            db_cooc.execute('''CREATE INDEX db_out.IDX_COND_ID on 
D (condition_concept_id)''')

            log.debug('Iterating conditions...')
            d=[db_cooc.execute('''select * from db_out.D 
where condition_concept_id={0}'''.format(cond_id)).fetchall() 
               for cond_id in cond_uid]
        else: # if to find out all about a condition
            log.fatal('Do not index by condition now. It can be very slow.')

        db_cooc.execute('detach db_out')

    return d

def GetPersonRecords(db, person_id):
    # get drug table
    cur=db.execute('''select  drug_concept_id as did, drug_exposure_start_date as ds, drug_exposure_end_date as de
from drug_exposure
where person_id={0}
order by did, ds, de'''.format(person_id))
    dt=cur.fetchall()

        # get condition table
    cur=db.execute('''select condition_concept_id as cid, condition_start_date as cs
from condition_occurrence
where person_id={0}
order by cid, cs'''.format(person_id))
    ct=cur.fetchall()

    return (dt, ct)

