import numpy as np

import dlansvd as dlan
import slansvd as slan

deps=np.finfo(np.float64).eps
seps=np.finfo(np.float32).eps

doption=np.array([np.sqrt(deps), deps**0.75, 0.0], dtype=np.float64)
soption=np.array([np.sqrt(seps), seps**0.75, 0.0], dtype=np.float32)
ioption=np.array([0, 1], np.int32)

def dlansvd(aprod, m, n, k, kmax = None, jobu = True, jobv = True, tol=1e-10, verbose=True):
    '''double precisian svd
    '''

    if kmax is None:
        kmax = min(m, n)

    u=np.zeros((m, kmax + 1), np.float64, 'F')
    v=np.zeros((n, kmax + 1), np.float64, 'F')
    s=np.zeros(kmax, np.float64, 'F')
    bnd=np.zeros(kmax, np.float64, 'F')

    lwrk=m + n + 13*kmax + 8*kmax**2 + 32*m + 8
    liwrk=8*kmax
    work=np.zeros(lwrk, np.float64)
    iwork=np.zeros(liwrk, np.int32)

    if verbose: dlan.clearstat()
    info = dlan.dlansvd('Y' if jobu else 'N', 'Y' if jobv else 'N',
                        m, n, k, kmax, u, s, bnd, v, tol, work, iwork, 
                        doption, ioption, np.zeros(0, np.float64), np.zeros(0, np.int32), aprod)
    if verbose: 
        dlan.printstat()
        print ' +- max(BND)={0}'.format(bnd[:k].max())

    if info > 0:
        raise RuntimeError('An invariant subspace of dimension {0} was found'.format(info))
    elif info < 0:
        raise RuntimeError('K singular triplets did not converge within kmax iterations')

    s=s[:k]
    u=u[:,:k]
    v=v[:,:k]

    return (u if jobu else None, s, v if jobv else None)

def slansvd(aprod, m, n, k, kmax = None, jobu = True, jobv = True, tol=1e-7, verbose=True):
    '''single precisian svd
    '''

    if kmax is None:
        kmax = min(m, n)

    u=np.zeros((m, kmax + 1), np.float32, 'F')
    v=np.zeros((n, kmax + 1), np.float32, 'F')
    s=np.zeros(kmax, np.float32, 'F')
    bnd=np.zeros(kmax, np.float32, 'F')

    lwrk=m + n + 13*kmax + 8*kmax**2 + 32*m + 8
    liwrk=8*kmax
    work=np.zeros(lwrk, np.float32)
    iwork=np.zeros(liwrk, np.int32)

    if verbose: slan.clearstat()
    info = slan.slansvd('Y' if jobu else 'N', 'Y' if jobv else 'N',
                        m, n, k, kmax, u, s, bnd, v, tol, work, iwork, 
                        soption, ioption, np.zeros(0, np.float32), np.zeros(0, np.int32), aprod)
    if verbose: 
        slan.printstat()
        print ' ++ max(BND)={0}'.format(bnd[:k].max())

    if info > 0:
        raise RuntimeError('An invariant subspace of dimension {0} was found'.format(info))
    elif info < 0:
        raise RuntimeError('K singular triplets did not converge within kmax iterations')

    s=s[:k]
    u=u[:,:k]
    v=v[:,:k]

    return (u if jobu else None, s, v if jobv else None)

def aprod(transA, m, n, x, y, dparm, iparm, xl, yl):

    if transA.lower()[0] == 't':
        y[:n]=np.dot(A.T, x[:m])
        return 1.0
    else:
        y[:m]=np.dot(A, x[:n])
        return 0.0

if __name__=='__main__':
    m = 1000
    n = 500
    k = 10

    oA = np.random.rand(m, n)

    A = oA.astype(np.float32)
    us, ss, vs = slansvd(aprod, m, n, k)
    A = oA.astype(np.float64)
    ud, sd, vd = dlansvd(aprod, m, n, k)

    u,s,v = np.linalg.svd(A)
    u=u[:,:k];    s=s[:k];    v=v[:k,:].T

    rd = np.dot(ud*sd, vd.T)
    rs = np.dot(us*ss, vs.T)
    r = np.dot(u*s, v.T)

    ond = max(np.fabs(np.dot(ud.T, ud) - np.eye(k)).max(), np.fabs(np.dot(vd.T, vd) - np.eye(k)).max())
    ons = max(np.fabs(np.dot(us.T, us) - np.eye(k)).max(), np.fabs(np.dot(vs.T, vs) - np.eye(k)).max())
    print('Orthnomality error   for double/single lansvd are %g / %g'%(ond, ons))
    print('Singular value error for double/single lansvd are %g / %g'%(
            (sd - s).max(), (ss - s).max()))
    print('Reconstruction error for double/single lansvd are %g / %g (truth = %g)'%(
            ((A - rd)**2).sum(), ((A - rs)**2).sum(), ((A - r)**2).sum()))
