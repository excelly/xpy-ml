import sqlite3 as sql

from ex.common import *
from ex.io.common import *
from ex.pp.common import *
import ex.array as ea

import base

InitLog()

def usage():
    print('''
generate table counts for OMOP

python --input={omop db file} [--output={output file}] [--poolsize={number of parallel processes}]
''')
    sys.exit(1)

def COOC(rd, rc, sw=0):
    return np.logical_and(rd[:, 1] <= rc[1], rd[:, 2] + sw >= rc[1])

def UpdateCounts(C, dt, ct, person, drug_list, cond_list, method='srsm', incident=False, sw=0):
    # dt: did, ds, de
    # ct: cid, cs

    if len(dt) == 0 and len(ct) == 0: return

    if len(dt) == 0:
        ct=arr(ct, dtype=np.int32).reshape(len(ct), 2)
        ct[:, 0]=EncodeArray(ct[:, 0].ravel(), cond_list)
        uc_idx=arguniqueInt(ct[:, 0])
        uc=ct[uc_idx, 0]
        if incident:
            ct=ct[uc_idx, :] # since ct is ordered by cid and cs
        btable, drow, ccol, n3=C

        for i in range(ct.shape[0]):
            # w11
            n3+=1
            ccol[ct[i, 0], 3] -= 1

    # w10
        for i in range(ct.shape[0]):
            c=ct[i, 0]
            ccol[c, 2] += 1

        return

    if len(ct) == 0:
        dt=arr(dt, dtype=np.int32).reshape(len(dt), 3)
        dt[:, 0]=EncodeArray(dt[:, 0].ravel(), drug_list)
        ud=uniqueInt(dt[:, 0])
        btable, drow, ccol, n3=C

        for i in range(dt.shape[0]):
            d=dt[i, 0]
        # w01
            drow[d, 1] += 1
            
        # w11
            n3+=1
            drow[d, 3] -= 1

        return

    dt=arr(dt, dtype=np.int32).reshape(len(dt), 3)
    ct=arr(ct, dtype=np.int32).reshape(len(ct), 2)
    dt[:, 0]=EncodeArray(dt[:, 0].ravel(), drug_list)
    ct[:, 0]=EncodeArray(ct[:, 0].ravel(), cond_list)

    ud=uniqueInt(dt[:, 0])
    uc_idx=arguniqueInt(ct[:, 0])
    uc=ct[uc_idx, 0]

    if incident:
        ct=ct[uc_idx, :] # since ct is ordered by cid and cs

    btable, drow, ccol, n3=C

    d_empty=np.ones(dt.shape[0], dtype=np.bool)
    c_empty=np.ones(ct.shape[0], dtype=np.bool)
    for i in range(dt.shape[0]):
        rd=dt[i, :]
        d=rd[0]
        for j in range(ct.shape[0]):
            rc=ct[j, :]
            if rd[1] <= rc[1] and rd[2] + sw >= rc[1]:
                c=ct[j, 0]
                d_empty[i]=False
                c_empty[j]=False

                # w00
                btable[d, c, 0] += 1

                # w01
                drow[d, 1] += 1
                btable[d, c, 1] -= 1

                # w11
                n3+=1
                drow[d, 3] -= 1
                ccol[c, 3] -= 1
                btable[d, c, 3] += 1

    for i in find(d_empty):
        d=dt[i, 0]
        # w01
        drow[d, 1] += 1
            
        # w11
        n3+=1
        drow[d, 3] -= 1

    for i in find(c_empty):
        # w11
        n3+=1
        ccol[ct[i, 0], 3] -= 1

    # w10
    for i in range(ct.shape[0]):
        c=ct[i, 0]
        ccol[c, 2] += 1

        filter=COOC(dt, ct[i, :])
        for d in ud:
            if filter[dt[:, 0] == d].any():
                btable[d, c, 2] -= 1

def MergeC(C):
    # merge marginals together
    btable, drow, ccol, n3=C
    C=btable.copy()

    for i in range(drow.shape[0]):
        for j in range(drow.shape[1]):
            C[i, :, j]+=drow[i, j]

    for i in range(ccol.shape[0]):
        for j in range(ccol.shape[1]):
            C[:, i, j]+=ccol[i, j]

    C[:, :, 3]+=n3

    return C

test_dt=[[[0, 0, 4],
          [0, 5, 9]],
          [[0, 1, 5],
          [1, 6, 10],
          [2, 11, 12]],
          [[2, 0, 4],
          [1, 2, 7]]]

test_ct=[[[0, 1],
          [0, 2],
          [0, 6]],
         [[0, 0],
          [0, 8]],
         [[1, 3],
          [1, 8],
          [0, 9]]]

if __name__ == '__main__':
    try:
        opts=getopt(sys.argv[1:], ['input=','output=','poolsize=', 
                                   'method=', 'incident=', 'nperson=', 'help'])
    except GetoptError as ex:
        usage()
    if opts.has_key('--help'): usage()

    input_db=os.path.abspath(opts.get('--input', 'OSIM.db3'))
    output_file=os.path.abspath(opts.get('--output', 'table_counts.pkl'))
    method=opts.get('--method', 'srsm')
    incident=bool(int(opts.get('--incident', 0)))
    nperson=int(opts.get('--nperson', 1e7))
    poolsize=int(opts.get('--poolsize', 1))

    if False:
        drug_list=np.arange(3, dtype=np.int32)
        cond_list=np.arange(2, dtype=np.int32)
        person_list=np.arange(3)

        n_drug=len(drug_list)
        n_cond=len(cond_list)
        n_person=len(person_list)

        C=(np.zeros((n_drug, n_cond, 4)),
           np.zeros((n_drug, 4)),
           np.zeros((n_cond, 4)),
           np.zeros(1))

        for person in person_list:
            dt=test_dt[person]
            ct=test_ct[person]

            UpdateCounts(C, dt, ct, person, drug_list, cond_list, 
                         method=method, incident=incident)

        C=MergeC(C)
        for i in range(n_drug):
            for j in range(n_cond):
                print i,j,C[i, j, :],C[i, j, :].sum()

        sys.exit(0)

    log.info("Gathering OMOP table counts using {0} processes".format(poolsize))
    log.info("Input={0}. Output={1}".format(input_db, output_file))

    db=GetDB(input_db, 1000)

    drug_list=base.GetUniqueDrugs(db, '', '')
    cond_list=base.GetUniqueConds(db, '', '')
    person_list=np.arange(nperson) + 1

    n_drug=len(drug_list)
    n_cond=len(cond_list)
    n_person=len(person_list)

    log.info("Handling {0} drugs, {1} conditins, {2} persons".format(
            n_drug, n_cond, n_person))

    C=(np.zeros((n_drug, n_cond, 4)),
       np.zeros((n_drug, 4)),
       np.zeros((n_cond, 4)),
       np.zeros(1))

    for person in person_list:
        dt, ct=base.GetPersonRecords(db, person)
        
        log.info("Person {0}: {1} Drug records and {2} Cond records".format(
                person, len(dt), len(ct)))

        UpdateCounts(C, dt, ct, person, drug_list, cond_list, method, incident)
    db.close()
    
    C=MergeC(C)

    tag="{0}_{1}".format(method, 'i' if incident else 'p')

    lines=[]
    for i in range(n_drug/10):
        d=drug_list[i]
        for j in range(n_cond/10):
            c=cond_list[j]

            cc=C[i, j, :]
            lines.append("{0},{1},{2},{3},{4},{5}".format(
                    d, c, cc[0], cc[1], cc[2], cc[3]))

        traceIter(i, 0, n_drug - 1)

    with xFile('tables_{0}_p{1}.csv'.format(tag, len(person_list)), 'w') as output:
        output.write('d_id, c_id, w_00, w_01, w_10, w_11\n')
        output.write("\n".join(lines))
