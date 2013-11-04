from factorization import *

from uv_rp import UVRP
from uv_online import UVOL

def AProd(trans, m, n, x, y = None, dparm = None, iparm = None, xl = None, yl = None):
    '''doing matrix product'''

    if isstr(trans): trans = trans[0] == 't'
    r = mul(A.T if trans else A, x)
    if y is not None: 
        if x.ndim == 1: y[:r.size] = r
        else: y[:r.shape[0], :r.shape[1]] = r
    return r

def AProd_D(trans, m, n, x, y = None, dparm = None, iparm = None, xl = None, yl = None):

    if isstr(trans): trans = trans[0] == 't'
    B = LoadPickles(mat_file)
    r = mul(B.T if trans else B, x)
    if y is not None: 
        if x.ndim == 1: y[:r.size] = r
        else: y[:r.shape[0], :r.shape[1]] = r
    return r

def ParseRow(line):
    line = line.strip().split('    ')
    line = [l for l in line if l != '']
    return arr(line, dtype = float64)

def AProd_R(trans, m, n, x, y = None, dparm = None, iparm = None, xl = None, yl = None):
    filename = '/auton/home/lxiong/data/deblending/isolated_spirals/isolated_spiral_set1'

    if isstr(trans): trans = trans[0] == 't'
    if x.ndim == 1: x = col(x)

    if trans: r = zeros((n, x.shape[1]))
    else: r = empty((m, x.shape[1]))

    with open(filename) as fin:
        log.info('Reading disk %s...' % ('T' if trans else ''))
        for ind in range(m):
            rr = ParseRow(fin.readline())
            if trans: r += outer(rr, x[ind])
            else: r[ind] = mul(rr, x)
            
    if y is not None: 
        if x.shape[1] == 1: y[:r.size] = r.ravel()
        else: y[:r.shape[0], :r.shape[1]] = r
        return 0
    else: 
        return r

def ASrc(A):
    ind = 0
    guard = len(A) - 1
    while True:
        yield A[ind]
        ind = ind + 1 if ind < guard else 0

def ASrc_D(mat_file):
    A = LoadPickles(mat_file)
    ind = 0
    guard = len(A) - 1
    while True:
        yield A[ind]
        ind = ind + 1 if ind < guard else 0

def ASrc_R(filename = '/auton/home/lxiong/data/deblending/isolated_spirals/isolated_spiral_set1', m = 100, n = 500**2):

    with open(filename) as fin:
        log.info('Reading disk...')
        ind = 0
        guard = m - 1
        while True:
            rr = ParseRow(fin.readline())
            check(len(rr) == n, 'wrong input')
            yield rr

            ind += 1
            if ind >= m: fin.seek(0, os.SEEK_SET)

def test_speed(k, d, type = 'm'):
    '''test the speed and accuracy of uv_rp
    '''
    
    m, n = A.shape

    if type == 'm': 
        aprod = AProd 
        asrc = ASrc(A)
    elif type == 'd': 
        aprod = AProd_D
        asrc = ASrc(A)
    else: 
        aprod = AProd_R
        asrc = ASrc_R()

    if d is not None:
        tA = n < m
        f = UVRP(n if tA else m, k, d)
        tic()
        U_rp, V_rp = f.Factorize(aprod, m, n, tA, verbose = False)
        t_rp = toc(show=False)
        err_rp=rmse(mul(U_rp.T, V_rp) - A)
#        print err_rp, t_rp
    else:
        err_rp = None
        t_rp = None

    if d <= 0 or d is None:
        f = UVOL(n, k)
        tic()
        V_ol = f.Factorize(asrc, m, int(ceil(m/100.0)), verbose = False)
        U_ol = solve(mul(V_ol, V_ol.T), mul(V_ol, A.T))
        t_ol = toc(show=False)
        err_ol=rmse(mul(U_ol.T, V_ol) - A)
#        print err_ol, t_ol

        tic()
        U_svd, S_svd, V_svd = dlansvd(aprod, m, n, k,verbose = False)
        t_svd = toc(show = False)
        err_svd=rmse(mul(U_svd*S_svd, V_svd.T) - A)
#        print err_svd, t_svd

    else:
        err_svd = None
        err_ol = None
        t_svd = None
        t_ol = None

    return (err_svd, t_svd, err_rp, t_rp, err_ol, t_ol)

if __name__ == '__main__':
    InitLog()

    ms = round(logspace(log10(200), log10(10000), 10))
    ks = round(logspace(log10(1), log10(50), 10))
    ds = round(logspace(log10(50), log10(300), 10))
    print ms, ks, ds

    err_svd = zeros((ms.size, ks.size))
    err_ol = zeros((ms.size, ks.size))
    err_rp = zeros((ms.size, ks.size, ds.size))
    t_svd = zeros((ms.size, ks.size))
    t_svdd = zeros((ms.size, ks.size))
    t_ol = zeros((ms.size, ks.size))
    t_old = zeros((ms.size, ks.size))
    t_rp = zeros((ms.size, ks.size, ds.size))
    t_rpd = zeros((ms.size, ks.size, ds.size))
    for ind in range(ms.size):
        n = m = ms[ind]

        rk = sqrt(m)
        A=mul(random.randn(m,rk), random.randn(rk, n)) + random.randn(m,n)*0.1*sqrt(m)
        mat_file = 'tmp_uv_fast_A.pkl'
        SavePickle(mat_file, A)
        
        for jnd in range(ks.size):
            k = ks[jnd]

            err_svd[ind,jnd], t_svd[ind,jnd], tmp, tmp, err_ol[ind,jnd], t_ol[ind,jnd] = test_speed(k, None, 'm')
            e_svd, t_svdd[ind,jnd], tmp, tmp, e_ol, t_old[ind,jnd] = test_speed(k, None, 'd')
            check(eq(e_svd, err_svd[ind,jnd], 1e-5), 'oops')
            check(eq(e_ol, err_ol[ind,jnd], 1e-5), 'oops')

            for knd in range(ds.size):
                d = ds[knd]

                log.info('M = %d, k = %d, d = %d' % (m, k, d))

                err_rp[ind,jnd,knd], t_rp[ind,jnd,knd] = test_speed(k, d, 'm')[2:4]
                t_rpd[ind,jnd,knd] = test_speed(k, d, 'd')[3]
                log.info('RMSE = %g | %g | %g, Time = %g | %g | %g, Disk Time = %g | %g | %g' % (
                        err_rp[ind,jnd,knd], err_ol[ind,jnd], err_svd[ind,jnd], 
                        t_rp[ind,jnd,knd], t_ol[ind,jnd], t_svd[ind,jnd], 
                        t_rpd[ind,jnd,knd], t_old[ind,jnd], t_svdd[ind,jnd]))

                SaveMat('uv_fast_benchmark.mat', {'ms':ms,'ks':ks,'ds':ds,'err_svd':err_svd,'err_rp':err_rp, 'err_ol':err_ol, 
                                                  't_svd':t_svd,'t_svdd':t_svdd, 't_rp':t_rp, 't_rpd':t_rpd, 't_ol':t_ol, 't_old':t_old})

############ sdss real

    ms = [50, 100, 250, 500]
    k=10
    err_svd = zeros(len(ms))
    t_svd = zeros(len(ms))
    err_rp = zeros(len(ms))
    t_rp = zeros(len(ms))
    err_ol = zeros(len(ms))
    t_ol = zeros(len(ms))
    for ind in range(len(ms)):
        src = ASrc_R(m = ms[ind])
        A = vstack([src.next() for ii in range(ms[ind])])
        m, n = A.shape
        del src

        err_svd[ind], t_svd[ind], err_rp[ind], t_rp[ind], err_ol[ind], t_ol[ind] = test_speed(k, 0, 'r')
        log.info('RMSE = %g | %g | %g, Time = %g | %g | %g' % (
                err_rp[ind], err_ol[ind], err_svd[ind], 
                t_rp[ind], t_ol[ind], t_svd[ind]))

        SaveMat('uv_fast_raw_perf.mat', {'ms':ms,'err_svd':err_svd,'err_rp':err_rp, 'err_ol':err_ol, 
                                        't_svd':t_svd, 't_rp':t_rp, 't_ol':t_ol})
