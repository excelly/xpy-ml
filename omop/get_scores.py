import os
import sys
import numpy as np
from random import uniform
import cPickle as pickle
import scipy.io as sio
from ex.plott import *

draw_figure=True

import getopt

def usage():
    print('''
generate the score for each d-c pair

python get_scores.py 
--in=raw_count_file 
--sub_out={0,1} output the score files for submission)
--mat_out={0,1} output the score matrix
--nous={0, 1} drop the unsurpported pairs or not
''')
    sys.exit(1)

def ReadCountTable(input_file):
    '''read in the raw counts file. cache them into a pickle
    '''

    pickle_file=os.path.basename(input_file) + '.pkl'
    
    if os.path.exists(pickle_file):
        with open(pickle_file) as stream:
            header, table=pickle.load(stream)
#        sio.savemat(os.path.basename(input_file) + '.mat', {'table':table}, do_compression=True)
        return (header, table)


    f=open(input_file, 'r')
    header=f.readline().rstrip('\n').split(',')
    if len(header) != 6:
        raise RuntimeError('wrong counts file')

    print 'Reading...'
    rows=f.readlines()
    f.close()

    print 'Converting...'
    table=np.zeros((len(rows), len(header)), dtype=np.float64)
    for i in range(len(rows)):
        table[i, :]=rows[i].split(',')

        if i % 1000000 == 0:
            print i, '/', len(rows)

    with open(pickle_file, 'w') as stream:
        pickle.dump((header, table), stream, 2)

    return (header, table)

def WriteScoreTable(score_table, output_file):
    '''output the result score file
    '''

    print 'Preparing output...'
    n=score_table.shape[0]
    lines=["%d,%d,%f\n" % (row[0], row[1], row[2]) 
           for row in score_table]
    print 'Writing...'
    with open(output_file, 'w') as f:
        f.write('d_id, c_id, predicted\n')
        f.writelines(lines)

def NormalizeScores(scores):
    '''normalize the score vector so that its in range [0, 1]
    '''
    
    return scores

    ma=scores.max()
    mi=scores.min()
    return (scores - mi)/(ma - mi)

def ScoreBCPNN(counts_table, prior=0.5):
    # did, cid, w00, w01, w10, w11

    n=counts_table.shape[0]
    W=counts_table[:, 2:]
    E=(W[:, 0] + W[:, 2])*(W[:, 0] + W[:, 1])/W.sum(1)
    IC=np.log((W[:, 0] + prior)/(E + prior))
    IC=NormalizeScores(IC)

    print W[0,:]
    print E
    print IC

    filter=E == 0
    ub=IC[~filter].min()
    nempty=filter.sum()
    rnd=np.random.rand(nempty).astype(IC.dtype)
    IC[filter]=ub-1-rnd

    stable=np.hstack((counts_table[:, 0:2], IC.reshape(n, 1)))
    return stable

def ScoreBCPNN_RandomU(counts_table, prior=0.5):
    # did, cid, w00, w01, w10, w11

    n=counts_table.shape[0]
    W=counts_table[:, 2:]

    i_s=W[:, 0] > 0
    ns=sum(i_s)
    nu=len(i_s) - ns

    if ns == 0:
        print 'No unsupported pairs found'
        return ScoreBCPNN

    Ws=W[i_s, :]
    Wu=W[~i_s, :]

    # supported pairs
    E=(Ws[:, 0] + Ws[:, 2])*(Ws[:, 0] + Ws[:, 1])/Ws.sum(1)
    IC=np.log((Ws[:, 0] + prior)/(E + prior))
    IC=NormalizeScores(IC)

    # unsupported
    scores=np.zeros(n)
    scores[i_s]=IC
    scores[~i_s]=-1 - np.random.rand(nu)
    scores=scores.reshape(n, 1)
        
    stable=np.hstack((counts_table[:, 0:2],
                      scores))

    return stable

def ScorePRR(counts_table, prior=1e-5):
    n=counts_table.shape[0]
    W=counts_table[:, 2:]

    nom=(W[:, 0])/(W[:, 0] + W[:, 1] + prior)
    den=(W[:, 2])/(W[:, 2] + W[:, 3] + prior)

    PRR=np.log((nom + prior)/(den + prior))
    PRR=NormalizeScores(PRR)

    stable=np.hstack((counts_table[:, 0:2], PRR.reshape(n, 1)))
    return stable

def GetTruthDict():
    '''get the dict for the groundtruth
    '''

    truth_file='OMOP_TRUE_RELATIONSHIPS.txt'
    f=open(truth_file)
    f.readline()
    lines=f.readlines()
    f.close()
    truth_dict={}
    for line in lines:
        fields=line.rstrip('\n').split('\t')
        truth_dict[(int(fields[0]), int(fields[1]))]=int(fields[2])

    return truth_dict

def GetTruth(dc):
    '''get a truth data for a given prediction table
    dc: the drug_cond pairs from the table, one pair per row
    '''
    truth_dict=GetTruthDict()

    n=dc.shape[0]
    has_truth=np.zeros(n, dtype=np.bool)
    truth=-np.ones(n, dtype=np.bool)

    print 'Merging truth...'
    for i in range(n):
        key=(int(dc[i, 0]), int(dc[i, 1]))
        if key in truth_dict:
            has_truth[i]=True
            truth[i]=truth_dict[key]
            truth_dict[key]=-1

    found=has_truth.sum()
    nmissing=len(truth_dict) - found
    print '%d/%d truth pairs found' % (found, len(truth_dict))

    if nmissing > 0:
        mp=[]
        for key, val in truth_dict.items():
            if val != -1: mp.append(val)

        missing_truth=np.array(mp, dtype=np.float32)
    else:
        missing_truth=None

    return (has_truth, truth, missing_truth)

def ComputePerf(scores, truth_tuple, tag):
    '''computer the performance
    '''

    scores=scores[truth_tuple[0]]
    labels=truth_tuple[1][truth_tuple[0]]

    if truth_tuple[2] is not None:
        n_missing=len(truth_tuple[2])
        scores=np.hstack((scores, -1e5*np.ones(n_missing)))
        labels=np.hstack((labels, truth_tuple[2]))

    N=len(labels)
    M=labels.sum()

    sidx=np.lexsort((labels, -scores))
    labels=labels[sidx]
    scores=scores[sidx]

    if draw_figure:
        fig=figure()
        subplot(fig, 121)
        plot(labels, '+')
        ss=scores
        ss[ss == -1e5]=0
        plot(ss)
        title(tag)

    def precision(K):
      return labels[0:K].mean()

    ap=np.zeros(N)
    for i in range(N):
        if labels[i] > 0.5:
            ap[i]=precision(i + 1)

    start=0
    while start < N:
        v=scores[start]
        end=start + 1
        while end < N and scores[end] == v:
            end += 1

        if end - start > 1:
            ap[start:end]=ap[end - 1]

        start=end

    ap=ap[labels > 0.5]

    if draw_figure:
        subplot(fig, 122)
        plot(ap, '+')
        title('AP = %f' % ap[ap >= 0].mean())

    ap=ap[ap >= 0].mean()

    print 'Score %s = %f' % (tag, ap)
    return ap

def BlendRank(scores1, scores2):
    sidx1=np.argsort(scores1)
    sidx2=np.argsort(scores2)

    score=(sidx1 + sidx2)*0.5
    print scores1
    print sidx1
    print scores1[sidx1]
    print scores2
    print sidx2
    print score
    return NormalizeScores(score)

def MakeScoreMatrix(counts_table, scores):
    d_id=np.int32(counts_table[:, 0] - 1)
    c_id=np.int32(counts_table[:, 1] - 1)
    has_sup=counts_table[:, 2] > 0

    m=d_id.max() + 1
    n=c_id.max() + 1
    mat=np.empty(m*n, dtype=np.float64)
    sup=np.empty(m*n, dtype=np.float32)
    mat[:]=np.nan
    sup[:]=np.nan

    idx=d_id*n + c_id
    mat[idx]=scores
    sup[idx]=has_sup

    truth=GetTruthDict()
    gt=[(item[0][0], item[0][1], item[1]) for item in truth.items()]
    gt=np.array(gt, dtype=np.int32)

    return {'mat':mat.reshape(m,n), 'support':sup.reshape(m, n), 
            'truth':gt}

def WriteMat(filename, obj):
    sio.savemat(filename, obj, 
                do_compression=True, oned_as='column')

if __name__ == '__main__':
    try:
        opts=getopt.getopt(sys.argv[1:], '', 
                           ['in=', 'sub_out=', 'mat_out=', 'nous=',
                            'help'])
    except:
        usage()
    opts=dict(opts[0])
    if opts.has_key('--help'):
        usage()

    input_file=opts['--in']
    output_base=os.path.basename(input_file)
    sub_out=bool(int(opts.get('--sub_out', '0')))
    mat_out=bool(int(opts.get('--mat_out', '0')))
    drop_unsupported=bool(int(opts.get('--nous', '0')))

    header, counts_table=ReadCountTable(input_file)
    n=counts_table.shape[0]
    print 'Read counts from {0}. # Pairs={1}:\nColumns: {2}'.format(
        input_file, n, header)

    filter=counts_table[:, 1] <= 4519
    counts_table=counts_table[filter, :]
 
    i_supported=counts_table[:, 2] > 0
    print '{0} with support \n{1} without support'.format(
        np.sum(i_supported), np.sum(~i_supported))

    if drop_unsupported:
        print 'Dropping unsupported pairs'
        counts_table=counts_table[i_supported, :]
        n=counts_table.shape[0]
        print '%d pairs left' % n
    
    truth=GetTruth(counts_table[:, 0:2])

    method='BCPNN'
    print method
    score_table=ScoreBCPNN(counts_table)
    sio.savemat('test.mat', {'score_table':score_table[truth[0], :]})
    ComputePerf(score_table[:, 2], truth, method)
    if sub_out:
        WriteScoreTable(score_table, '{0}.{1}.scores'.format(output_base, method))
    if mat_out:
        WriteMat('{0}.{1}.scores.mat'.format(output_base, method),
                 MakeScoreMatrix(counts_table, score_table[:, 2]))

    # method='BCPNN_RandomU'
    # print method
    # score_table=ScoreBCPNN_RandomU(counts_table, 0.4)
    # ComputePerf(score_table[:, 2], truth, method)
    # if sub_out:
    #     WriteScoreTable(score_table, '{0}.{1}.scores'.format(output_base, method))

    # method='PRR'
    # print method
    # score_table_prr=ScorePRR(counts_table)
    # ComputePerf(score_table_prr[:, 2], truth, method)
    # if sub_out:
    #     WriteScoreTable(score_table_prr, '{0}.{1}.scores'.format(output_base, method))
    # if mat_out:
    #     WriteMat('{0}.{1}.scores.mat'.format(output_base, method),
    #              MakeScoreMatrix(counts_table, score_table_prr[:, 2]))

    # method='BCPNN_PRR'
    # print method
    # score_table_bcprr=score_table.copy()
    # score_table_bcprr[:, 2] = BlendRank(score_table[:, 2], 
    #                                     score_table_prr[:, 2])
    # ComputePerf(score_table_bcprr[:, 2], truth, method)
    # if sub_out:
    #     WriteScoreTable(score_table_bcprr, '{0}.{1}.scores'.format(
    #             output_base, method))
    # if mat_out:
    #     WriteMat('{0}.{1}.scores.mat'.format(output_base, method),
    #              MakeScoreMatrix(counts_table, score_table_bcprr[:, 2]))

    if draw_figure:
        show()
