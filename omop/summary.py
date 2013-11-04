import os
import sys
import logging as log
from getopt import getopt

import ex.util as eu
from OMOP import OMOP
import base

eu.InitLog()

def usage():
    print('''summarize the OMOP data set

    python summary.py --modifier={''} --folder={''} --simulated --help
    ''');
    sys.exit(1);

try: options=dict(getopt(sys.argv[1:], '', ['modifier=', 'folder=', 'simulated', 'help'])[0])
except Exception as ex: 
    print(ex)
    usage()

if options.has_key('--help'): usage()

modifier=options.get('--modifier', '')
if len(modifier) > 0: modifier = '_' + modifier
folder=options.get('--folder', 'OSIM' + modifier)
simulated=options.has_key('--simulated')

if not os.path.exists(folder):
    print("Folder {0} not exist.".format(folder))
    sys.exit(1);

cond_src_dict={0: "Background\t\t",
               1: "Indication\t\t",
               2: "Drug outcome\t\t",
               3: "Indication outcome\t"}

ds=OMOP(modifier, folder)

log.info("Summarizaton begin...")

db=ds.GetDB()
db_cooc=ds.GetDB("COOC")
db_cond=ds.GetDB("COND")

log.info("==================== PERSON")

d=db.execute('''SELECT COUNT(person_id) from person''').fetchall()
n_person=d[0][0]
print('# Person = {0}'.format(n_person))

d=db.execute('''SELECT SUBSTR(year_of_birth,1,3), COUNT(person_id) 
FROM person
group by SUBSTR(year_of_birth,1,3)''').fetchall()
out=["- {0}0:\t{1} ({2:.4}%)".format(row[0], row[1], row[1]*100.0/n_person) for row in d]
print('---------- Person age portion')
print('\n'.join(out))

d=db.execute('''SELECT source_gender_code, COUNT(person_id) 
FROM person
group by source_gender_code''').fetchall()
out=["- {0}:\t{1} ({2:.4}%)".format(row[0], row[1], row[1]*100.0/n_person) for row in d]
print('---------- Person gender portion')
print('\n'.join(out))

d=db.execute('''SELECT source_race_code, COUNT(person_id) 
FROM person
group by source_race_code''').fetchall()
out=["- {0}:\t{1} ({2:.4}%)".format(row[0], row[1], row[1]*100.0/n_person) for row in d]
print('---------- Person race portion')
print('\n'.join(out))

log.info("==================== Observation period")

d=db.execute('''SELECT COUNT(DISTINCT person_id) from observation_period''').fetchall()
n_person_observed=d[0][0]
print('# Person observed = {0} ({1:.4}%)'.format(
        n_person_observed, n_person_observed*100.0/n_person))

d=db.execute('''SELECT AVG(observation_end_date - observation_start_date) 
from observation_period
where observation_end_date > 1000
and observation_start_date > 1000''').fetchall()
average_ob_length=d[0][0] / (3600*24*30.0)
print('Average observation length = {0:.4} months'.format(average_ob_length))

log.info("==================== Drug exposure")

drug_uid=ds.GetUniqueDrugs()[0]
n_drug=len(drug_uid)
print('# Drug = {0}'.format(n_drug))

d=db.execute('''SELECT COUNT(DISTINCT person_id) 
from drug_exposure''').fetchall()
n_person_exposed=d[0][0]
print('# Person exposed = {0} ({1:.4}%)'.format(
        n_person_exposed, n_person_exposed*100.0/n_person))

d=db.execute('''SELECT COUNT(drug_exposure_id) 
from drug_exposure''').fetchall()
n_exposure=d[0][0]
print('# Exposure = {0} ({1:.4} per Person, {2:.4} per Drug)'.format(
        n_exposure, n_exposure*1.0/n_person_exposed, n_exposure*1.0/n_drug))

d=db.execute('''SELECT AVG(drug_exposure_end_date - drug_exposure_start_date)
from drug_exposure
where drug_exposure_end_date > 1000
and drug_exposure_start_date > 1000''').fetchall()
average_exposure_length=d[0][0] / (3600*24*30.0)
print('Average exposure length = {0:.4} months'.format(
        average_exposure_length))

log.info("==================== Condition occurrence")

cond_uid=ds.GetUniqueConds()[0]
n_cond=len(cond_uid)
print('# Condition = {0}'.format(n_cond))

d=db.execute('''SELECT COUNT(DISTINCT person_id) 
from condition_occurrence''').fetchall()
n_person_with_conditions=d[0][0]
print('# Person with conditions = {0} ({1:.4}%)'.format(
        n_person_with_conditions, n_person_with_conditions*100.0/n_person))

d=db.execute('''SELECT COUNT(condition_occurrence_id) 
from condition_occurrence''').fetchall()
n_occurrence=d[0][0]
print('# Occurrence = {0} ({1:.4} per Person, {2:.4} per Condition'.format(
        n_occurrence, n_occurrence*1.0/n_person_with_conditions, n_occurrence*1.0/n_cond))

d=db_cond.execute('''SELECT AGE, count(condition_occurrence_id) 
from COND
group by AGE''').fetchall()
out=["- {0}0:\t{1} ({2:.4}%)".format(row[0], row[1], row[1]*100.0/n_occurrence) for row in d]
print('---------- Condition age portion')
print('\n'.join(out))

d=db_cond.execute('''SELECT gender_concept_id, count(condition_occurrence_id) 
from COND
group by gender_concept_id''').fetchall()
out=["- {0}:\t{1} ({2:.4}%)".format(row[0], row[1], row[1]*100.0/n_occurrence) for row in d]
print('---------- Condition gender portion')
print('\n'.join(out))

d=db_cond.execute('''SELECT race_concept_id, count(condition_occurrence_id) 
from COND
group by race_concept_id''').fetchall()
out=["- {0}:\t{1} ({2:.4}%)".format(row[0], row[1], row[1]*100.0/n_occurrence) for row in d]
print('---------- Condition race portion')
print('\n'.join(out))

if simulated:
    print("---------- Condition source portion:")
    d=db.execute('''select A_TYPE, count(CONDITION_OCCURRENCE_ID) 
from CONDITION_OCCURRENCE 
group by A_TYPE''').fetchall()
    out=["- {0}:\t{1} ({2:.4}%)".format(cond_src_dict[row[0]], row[1], row[1]*100.0/n_occurrence) for row in d]
    print('\n'.join(out))

log.info("==================== COOC")

d=db_cooc.execute('''SELECT COUNT(DISTINCT condition_concept_id) 
from cooc_drug''').fetchall()
n_cond_cooc=d[0][0]
print('# Conditions in COOC = {0} ({1:.4}%)'.format(
        n_cond_cooc, n_cond_cooc*100.0/n_cond))

d=db_cooc.execute('''SELECT COUNT(DISTINCT drug_concept_id) 
from cooc_drug''').fetchall()
n_drug_cooc=d[0][0]
print('# Drugs in COOC = {0} ({1:.4}%)'.format(
        n_drug_cooc, n_drug_cooc*100.0/n_drug))

d=db_cooc.execute('''SELECT COUNT(DISTINCT person_id) 
from cooc''').fetchall()
n_person_cooc=d[0][0]
print('# Person in COOC = {0} ({1:.4}%)'.format(
        n_person_cooc, n_person_cooc*100.0/n_person))

try:
    d=db_cooc.execute('''SELECT COUNT(condition_concept_id) 
from cooc''').fetchall()
    n_cooc=d[0][0]
    print('# COOC = {0} ({1:.4} per Person, {2:.4} per Drug, {3:.4} per Condition)'.format(
            n_cooc, n_cooc*1.0/n_person_cooc, n_cooc*1.0/n_drug_cooc, n_cooc*1.0/n_cond_cooc))
except ZeroDivisionError:
    print('! No COOC pairs can be found.')

if simulated:
    print("---------- COOC Condition source portion:")
    d=db_cooc.execute('''select A_TYPE, count(CONDITION_CONCEPT_ID) 
from COOC 
group by A_TYPE''').fetchall()
    out=["- {0}:\t{1} ({2:.4}%)".format(cond_src_dict[row[0]], row[1], row[1]*100.0/n_occurrence) for row in d]
    print('\n'.join(out))

log.info("Summarization done.")

db.close()
db_cond.close()
db_cooc.close()
