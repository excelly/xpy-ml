from common import *

def SThresh(A, thresh, l0=False):
    '''soft-thresholding
    '''

    if A.ndim == 1: A = row(A)

    if l0:
        ij=find(A**2 > 2*thresh)

        if ij[0].size > 0.3*A.size:
            B=zeros_like(A)
            B[ij]=A[ij]
        else:
            B=ssp.csr_matrix((A[ij], vstack(ij)), A.shape)
    else:
        ij1=find(A > thresh)
        ij2=find(A < -thresh)

        if ij1[0].size + ij2[0].size > 0.3*A.size:
            B=zeros_like(A)
            B[ij1]=A[ij1] - thresh
            B[ij2]=A[ij2] + thresh
        else:
            val=cat((A[ij1] - thresh, A[ij2] + thresh))
            sub=hstack((vstack(ij1),vstack(ij2)))
            B=ssp.csr_matrix((val.flatten(), sub), A.shape)

    return B

def SThreshRow(A, thresh, l0=False):
    '''soft-thresholding for rows
    '''

    if A.ndim == 1: A = row(A)

    m, n = A.shape
    ssA = sos(A, 1)

    if l0: ii=L2I(ssA > 2*thresh)
    else: ii=L2I(sqrt(ssA) > thresh)

    if len(ii) > 0.3*m: B=zeros(A.shape, A.dtype)
    else: B=ssp.lil_matrix(A.shape)

    if len(ii) > 0:
        if l0: B[ii,:]=A[ii,:]
        else: B[ii,:]=scale(A[ii,:], 1 - thresh/col(ssA[ii]), 1)

    return B

def SThreshCol(A, thresh, l0=False):
    '''soft-thresholding for rows
    '''

    if A.ndim == 1: A = row(A)

    m, n = A.shape
    ssA = sos(A, 0)

    if l0: ii=L2I(ssA > 2*thresh)
    else: ii=L2I(sqrt(ssA) > thresh)

    if len(ii) > 0.3*n: B=zeros((n, m), A.dtype)
    else: B=ssp.lil_matrix((n, m))

    if len(ii) > 0:
        if l0: B[ii,:]=A[:, ii]
        else: B[ii,:]=scale(A[:, ii], 1 - thresh/col(ssA[ii]), 0)

    return B.T

if __name__ == '__main__':
    InitLog()
    A = arange(11) - 5
    B = SThresh(A, 4.5)
    test((fabs(arr(B)) > 0).sum() == 2, 'SThresh')

