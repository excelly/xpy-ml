import sqlite3 as sql

from ex.common import *
from ex.io.common import *
from ex.pp.common import *
import ex.array as ea

import base

InitLog()

def usage():
    print('''
generate histograms for omop drugs

python --input={omop db file} [--output={output file}] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

def GetAge(y):
    if y == u'':
        return y
    else:
        return int(floor((2010 - y)/10.))

def GetHistAgeGender(db, drug_id):
    hist=db.execute('''
select GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID, count(PERSON_ID)
from DEP_D
where 
    DRUG_CONCEPT_ID={0}
group by 
    GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID;
'''.format(drug_id)).fetchall()

    r={}
    for age, gender, c in hist:
        r[(age, gender)]=c
    return r

age_code={0:0, 1:1, 2:2, 3:3, 4:4, 5:5,
          6:6, 7:7, 8:8, 9:9, 10:10, u'':11}
age_groups=range(11)
age_groups.append('M')
gender_code={8507:0, 8532:1, u'':2}
gender_groups=[8507, 8532, 'M']

def Counts2Table(counts):
    table=np.zeros((len(age_code), len(gender_code)))
    for key, val in counts.items():
        age, gender=key
        table[age_code[key[0]], gender_code[key[1]]] += val
    return table

if __name__ == '__main__':
    try:
        opts=getopt(sys.argv[1:], ['input=','output=','poolsize=', 'help'])
    except GetoptError as ex:
        usage()
    if opts.has_key('--help'): usage()

    input_db=os.path.abspath(opts.get('--input', 'OSIM.db3'))
    output_file=os.path.abspath(opts.get('--output', 'table_counts.pkl'))
    poolsize=int(opts.get('--poolsize', 1))

    log.info("Gathering OMOP drug histograms using {0} processes".format(poolsize))
    log.info("Input={0}. Output={1}".format(input_db, output_file))

    db=GetDB(input_db, 1000)
    db.create_function("GetAge", 1, GetAge)
    log.info('Get person list')
    cur=db.execute("select PERSON_ID, YEAR_OF_BIRTH, GENDER_CONCEPT_ID from PERSON")
    person_list=cur.fetchall()

    with xFile('person.txt', 'w') as output:
        output.write('p_id, age_group, gender\n')
        for row in person_list:
            row=list(row)
            row[1]=GetAge(row[1])
            if row[1] == u'': row[1]='M'
            if row[2] == u'': row[2]='M'
            output.write('{0},{1},{2}\n'.format(
                    row[0], row[1], row[2]))

#     hist_all_person=db.execute('''
# select GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID, count(PERSON_ID)
# from PERSON
# group by 
#     GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID;
# ''').fetchall()
#    r={}
#    for age, gender, c in hist_all:
#        r[(age, gender)]=c
#    hist_all_person=r

#     hist_all_de=db.execute('''
# select GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID, count(PERSON_ID)
# from DEP
# group by 
#     GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID;
# ''').fetchall()
#     r={}
#     for age, gender, c in hist_all_de:
#         r[(age, gender)]=c
#     hist_all_de=r

#     hist_all_de=db.execute('''
# select GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID, count(PERSON_ID)
# from PERSON
# group by 
#     GetAge(YEAR_OF_BIRTH), GENDER_CONCEPT_ID;
# ''').fetchall()
#    r={}
#    for age, gender, c in hist_all:
#        r[(age, gender)]=c
#    hist_all=r

    # log.info("Joining DE and P...")
    # db.execute("attach 'DEP.db3' as o")
#     db.execute('''
# create table o.DEP as 
# select d.DRUG_CONCEPT_ID as DRUG_CONCEPT_ID, d.DRUG_EXPOSURE_START_DATE as DRUG_EXPOSURE_START_DATE, d.DRUG_EXPOSURE_END_DATE as DRUG_EXPOSURE_END_DATE, p.PERSON_ID as PERSON_ID, p.YEAR_OF_BIRTH as YEAR_OF_BIRTH, p.GENDER_CONCEPT_ID as GENDER_CONCEPT_ID
# from 
#     PERSON as p cross join DRUG_EXPOSURE as d 
# where 
#     p.PERSON_ID=d.PERSON_ID;
# ''')
    # db.close()

    db=GetDB('DEP.db3', 2000)
#     log.info("Sorting...")
#     db.execute('''
# create table DEP_D as 
# select * 
# from 
#     DEP
# order by
#     DRUG_CONCEPT_ID;
# ''')
#     log.info("Indexing...")
#     db.execute("create index IDX_DEPD_DRUG_ID on DEP_D (DRUG_CONCEPT_ID)")

    # get the histgrams
    db.create_function("GetAge", 1, GetAge)

    drug_list=base.GetUniqueDrugs(db, '', '').tolist()
    n_drug=len(drug_list)
    log.info("Handling {0} drugs.".format(n_drug))

    # counts=[]
    # for d in drug_list:
    #     counts.append(GetHistAgeGender(db, d))
    #     log.info("Drug {0}: Age={1}".format(d, counts[-1]))
    # counts=dict(zip(drug_list, counts))
    # counts[-1]=hist_all
    # SavePickles("counts.pkl", [counts])

    counts=LoadPickles("counts.pkl")
    hists={}
    for drug, c in counts.items():
        hist=Counts2Table(c)
        hists[drug]=hist

    SavePickles("hists.pkl", [{"age_code": age_code,
                               "gender_code": gender_code,
                               "hists": hists}])

    with xFile('hists.txt', 'w') as output:
        output.write('d_id')
        for a in age_groups:
            for g in gender_groups:
                output.write(',{0}-{1}'.format(a, g))
        output.write('\n')
                
        for drug, h in hists.items():
            output.write('{0}, {1}\n'.format(drug, str(h.ravel().tolist())[1:-1]))
