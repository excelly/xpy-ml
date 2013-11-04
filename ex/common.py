import os, sys, time, math
import getopt
import logging as log
import logging.config
import traceback
import copy as pycopy
from subprocess import Popen, call, check_call, PIPE, STDOUT
from pdb import set_trace as dbstop

import numpy as np
import scipy as sp

from numpy import random, floor, ceil, round, fabs, sum, inf, nan, isinf, isnan, int32, int64, float32, float64, ndarray, matrix, ones, ones_like, zeros, zeros_like, empty, empty_like, eye, concatenate as cat, hstack, vstack, arange, diff, minimum, maximum, pi, tile as repmat, sort, argsort, sqrt, reshape, diag, linspace, logspace, log10, log2, log as ln, exp, sin, cos, argmax, argmin, unique, inner, outer, cumsum, trace, dot, kron
from numpy.random import rand, randn
from numpy.linalg import inv, svd, eig, eigh, solve, cholesky as chol, lstsq, norm, pinv, det
from scipy.linalg import qr, lu
import scipy.sparse as ssp

eps = np.finfo(np.float64).eps
feps = np.finfo(np.float32).eps
logsafe = eps

import exc

#################################################
# common utilities
#################################################

def xBase():
    '''Return the base path of my python files.
    '''

    return(os.environ.get('xPYTHONPATH', os.path.abspath('/auton/home/lxiong/h/python')))

def InitLog(level = None):
    '''initialize the logging
    '''
    
    log_config = os.path.join(xBase(), 'logging.conf')
    if not os.path.exists(log_config):
        raise RuntimeError("cannot find the log config at {0}".format(log_config))
    logging.config.fileConfig(log_config)

    if level is not None:
        log.root.setLevel(level)

def CmdArgs(args, long_options, usage = None):
    '''wrapper for python's getopt. accepts only long options, and return a dict.
    '''

    long_options.append('help')
    try:
        opts = dict(getopt.getopt(args, '', long_options)[0])
    except getopt.GetoptError as e:
        log.warn('GetoptError: {0}'.format(e))
        if usage is not None: usage()
        else: print e
        sys.exit(1)

    if opts.has_key('--help'): 
        if usage is not None: usage()
        sys.exit(0)

    return opts

def DictGet(d, *args):
    ''' get multiple values from a dictionary

    the *args should be "key1, defaut val1, key2, default val2, ...". or it can be [key1, key2, ...]
    '''
    
    if d is None: d = {}

    if islist(args[0]) or istuple(args[0]):
        key_list = args[0]
        return [d[key] for key in key_list]
    else:
        check(len(args) % 2 == 0, 'input must be pairs')
        result = [d.get(args[i*2], args[i*2 + 1]) 
                  for i in range(len(args)/2)]
        if len(result) == 1: result = result[0]
        return result

def GetOptions(options, *args):
    return DictGet(options, *args)

def colortext(text, c):
    '''make colorful text for certain terminals
    '''

    if c == 'y':
        return '\033[93m' + text + '\033[0m'
    elif c == 'r':
        return '\033[91m' + text + '\033[0m'
    elif c == 'g':
        return '\033[92m' + text + '\033[0m'
    else:
        raise ValueError('unsupported color')

def check(cond, msg = "", fatal = True):
    '''Check if all of the cond is satisfied.
    
    cond -- the conditions to check
    msg -- the msg to show if check failed
    fatal -- if this check is fatal (default True)
    '''

    if isinstance(cond, np.ndarray):
        cond=cond.all()
    elif hasattr(cond, "__iter__"):
        cond=all(cond)

    if not bool(cond): oops(msg, True, fatal)

def test(cond, name = "Test"):
    '''unittest facility
    
    cond -- the conditions to check
    name -- name of the test
    '''

    if isinstance(cond, np.ndarray):
        cond=cond.all()
    elif hasattr(cond, "__iter__"):
        cond=all(cond)

    if bool(cond):
        log.info("Passed: {0}".format(name))
    else:
        log.warn(colortext("Failed: {0}".format(name), 'r'))

def pause():
    '''ask the user to confirm before continue
    '''

    try: 
        raw_input("Press Enter to continue. EOF to exit.")
    except EOFError: 
        sys.exit(1)

em_tictoc_start_times = {}

def tic(tag = None):
    '''matlab's tic()
    '''

    global em_tictoc_start_times
    em_tictoc_start_times[tag] = time.time()

def toc(tag = None, msg = "", show = True):
    '''matlab's toc()
    '''

    global em_tictoc_start_times
    time_elapsed = time.time() - em_tictoc_start_times[tag]

    if show:
        if msg == "": msg = tag

        if time_elapsed < 300:
            print("<{0}>: Time elapsed: {1:0.5} sec".format(msg,time_elapsed))
        elif time_elapsed < 18000:
            print("<{0}>: Time elapsed: {1:0.3} min".format(msg,time_elapsed/60.0))
        else:
            print("<{0}>: Time elapsed: {1:0.3} hr".format(msg,time_elapsed/3600.0))

    return time_elapsed

def choose(cond, r_t, r_f):
    '''if cond, then return r_t else return r_f
    '''

    if isinstance(cond, np.ndarray):
        cond=cond.all()
    elif hasattr(cond, "__iter__"):
        cond=all(cond)

    return r_t if bool(cond) else r_f

def eq(a,b,tol = 1e-7):
    '''check if a==b within the error tolerance
    '''

    return fabs(a - b) <= tol

def oops(msg, show_stack = False, fatal = False):
    '''say oops for something un-expected
    '''

    if fatal:
        raise RuntimeError(msg)
    else:
        log.warn(msg)
        if show_stack: traceback.print_stack()

def TraceIter(cur, first, last):
    '''print text to trace the progress of iterations
    '''

    now=cur - first + 1
    perc=int(floor(100.*now/(last - first + 1)))

    if now == 1:
        print '  {0}%'.format(perc),
    else:
        if perc < 10:
            print '\b\b\b{0}%'.format(perc),
        else:
            print '\b\b\b\b{0}%'.format(perc),

        if cur >= last:
            print ''

    sys.stdout.flush()

def Partition(l, chunk_size = None, n_chunk = None):
    '''aggregate the elements in l into chunks.
    '''

    n = len(l)

    if chunk_size is None:
        chunk_size = ceil(n*1.0/n_chunk);
    chunk_size = int(chunk_size)

    r = []
    start = 0
    while start < n:
        end = min(n, start + chunk_size)
        r.append(l[start:end])
        start = end

    return r

def Flatten(l):
    '''flatten the list. only the first level lists are expanded.
    '''

    r = []
    for e in l:
        if isinstance(e, list): r.extend(e)
        else: r.append(e)
    return r

def CopyAtt(src, dest):
    '''copy src's attributes to dest
    '''

    if not isdict(src):
        src = src.__dict__

    for key, val in src.items():
        dest.__dict__[key] = pycopy.deepcopy(val)

def isstr(o):
    return isinstance(o, str)

def islist(o):
    return isinstance(o, list)

def istuple(o):
    return isinstance(o, tuple)

def isdict(o):
    return isinstance(o, dict)

def unzip(l):
    return [list(a) for a in zip(*l)]

#################################################
# computation utilities
#################################################

def isarray(A):
    '''return if A is an ndarray
    '''
    return isinstance(A, ndarray) and not isinstance(A, matrix)

def ismatrix(A):
    '''return if A is an matrix
    '''
    return isinstance(A, matrix)

def issparse(A):
    '''return if A is an sparse matrix
    '''
    return ssp.isspmatrix(A)

def nnz(A):
    '''return the number of nonzeros
    '''

    if ssp.isspmatrix(A):
        return A.nnz
    else:
        return A.nonzero()[0].size

def arr(a, dtype = None, order = None):
    '''convert anything into an array
    '''

    if ssp.isspmatrix(a): a = a.todense()
    return np.asarray(a, dtype, order)

def vec(a, dim = 1):
    '''convert an array into a vector
    if dim = 0, convert to row vector. if dim = 1, convert to col vector
    '''

    a = arr(a)
    return a.reshape((a.size, 1)) if dim == 1 else a.reshape(1, a.size)

def row(a):
    '''convert an array into a column
    '''

    a = arr(a)    
    return a.reshape((1, a.size))

def col(a):
    '''convert an array into a column
    '''

    a = arr(a)
    return a.reshape((a.size, 1))

def resize(a, new_shape, val = 0):
    '''resize the array
    '''

    if a.ndim == 1 and isinstance(new_shape, int): 
        r = ones(new_shape, a.dtype)*val if val != 0 else zeros(new_shape, a.dtype)
        r[:min(len(r), len(a))] = a
    else:
        r = ones(new_shape, dtype = a.dtype)*val if val != 0 else zeros(new_shape, dtype = a.dtype)
        r[:min(r.shape[0], a.shape[0]), :min(r.shape[1], a.shape[1])] = a

    return r

def sos(A, axis = None):
    '''return the sum of squares of A
    '''

    return emul(A, A).sum(axis)

def rmse(err):
    '''return the square-root of mean squared error
    '''

    return sqrt(emul(err,err).mean())

def quantile(x, q):
    '''return the q quantile of elements in x
    '''

    check(q <= 1 and q >= 0, 'quantile must be in [0,1]')

    x = sort(x.ravel())
    return x[int(round(q*(len(x)-1)))]

def find(a):
    ''' return tuple (i, j, k...)
    '''

    ij = a.nonzero()
    if len(ij) == 0: ij = (arange(0),)*a.ndim

    if len(ij) == 1: return ij[0]
    else: return ij

def shift(A, m = None, dim = 0):
    '''shift columns or columns of A
    dim = 0 for columns, otherwise for rows
    '''

    return A + vec(m, dim)

def scale(A, s, dim = 0):
    '''scale columns or columns of A
    dim = 0 for columns, otherwise for rows
    '''

    ii = isinf(s)
    if ii.any():
        oops('singular scalers found')
        s[ii] = 1

    if A.size == 0 or s.size == 0:
        return A.copy()

    if ssp.isspmatrix(A):
        if dim == 0: return mul(A, spdiag(s))
        else: return mul(spdiag(s), A)
    else:
        return A * vec(s, dim)

def emul(A, B):
    '''unified element-wise matrix multiplication

    if one them is sparse, return type is type(first sparse argument)
    if both dense, return array.
    '''

    if ssp.isspmatrix(A):
        if ssp.isspmatrix(B):#sparse .* sparse
            return A.multiply(B)
        else:#sparse .* dense
            return A.__class__(A.multiply(B))
    else:
        if ssp.isspmatrix(B):#dense .* sparse
            return B.multiply(A) 
        else:#dense .* dense
            return np.multiply(A, B)

def mul(A, B):
    '''unified matrix multiplication

    if both are sparse, the result is sparse. otherwise the result is
    an array
    '''

    if isarray(A) and isarray(B):
        return dot(A, B)
    else:
        return A*B

def emin(arrays, array2 = None):
    '''element-wise minimum
    '''

    if array2 is None:
        return reduce(minimum, arrays)
    else:
        return minimum(arrays, array2)

def emax(arrays, array2 = None):
    '''element-wise maximum
    '''

    if array2 is None:
        return reduce(maximum, arrays)
    else:
        return maximum(arrays, array2)

def GetOrder(A):
    '''get the ordering char of an array
    '''

    if A.flags["C_CONTIGUOUS"]:
        return('C')
    elif A.flags["F_CONTIGUOUS"]:
        return('F')
    else:
        raise RuntimeError("ex error", "strange array ordering")

def IsCont(A):
    '''if the array is continguous
    '''

    if A.flags["C_CONTIGUOUS"] or A.flags["F_CONTIGUOUS"]:
        return True
    else:
        return False

def MakeCont(A):
    '''make A C-continguous
    '''

    return np.ascontiguousarray(A)

def sub2ind(A, I, J, order = None):
    '''emulating matlab sub2ind. support 2D arrays only.

    A: target array.
    I: row index.
    J: column index.
    order: data layout of A. use "C","F", None (same as input A).'''

    if order is None: order = GetOrder(A).lower()
    I = arr(I)
    J = arr(J)
    
    if isinstance(A, tuple):
        m, n = A
    else:
        m, n = A.shape

    if order == 'c':
        return(I*n + J)
    else:
        return(I + J*m)

def ind2sub(A, ind, order = None):
    '''emulating matlab ind2sub. support 2D arrays only.

    A: target array.
    ind: linear index.
    order: data layout of A. use "C","F",None (same as input A).'''

    if order is None: order = GetOrder(A).lower()
    ind = row(ind)

    if isinstance(A, tuple): m, n = A
    else: m, n = A.shape

    if order == 'c':
        I = ind // n
        J = ind % n
    else:
        I = ind % m
        J = ind // m

    return vstack((I, J))

def MeanCov(X, weights = None, ridge = 0):
    ''' get the mean and covariance of X
    '''

    n, dim = X.shape
    if weights is None:
        m = X.mean(0)
        cX = X - m
        cov = mul(cX.T, cX)/n
    else:
        sw = weights.sum()
        m = mul(weights, X)/sw
        cX = X - m
        cov = mul(cX.T*weights, cX)/sw

    return (m, cov + eye(dim)*ridge)

def AssembleVector(input, field_name = None):
    '''assemble the specified field in input into a long vector
    if field_name is not specified, the input itself is assembled
    '''

    if field_name is not None:
        input = [arr(ii[field_name]).ravel() for ii in input]
    else:
        input = [arr(ii).ravel() for ii in input]

    return hstack(input)

def AssembleMatrix(input, field_name = None, by = 'row'):
    '''assemble the specified field in input into a long vector
    if field_name is not specified, the input itself is assembled
    '''

    if field_name is not None:
        input = [arr(ii[field_name]) for ii in input]
    else:
        input = [arr(ii) for ii in input]

    if by == 'row': return vstack(input)
    elif by == 'col': return hstack(input)
    else: raise ValueError('unknown combining direction')

def SetDiag(A, v):
    ii = arange(min(A.shape))
    A.ravel()[sub2ind(A, ii, ii)] = v
    return A

def spdiag(data):
    '''short-cut for spdiags
    '''

    data = arr(data)
    return(ssp.spdiags(data, 0, data.size, data.size))

def spmask(A, mask):
    '''extract a sparse matrix from A by masking.

    A: original dense array/matrix
    mask: sparse mask
    
    returned is a type(mask) sparse matrix
    '''

    check(A.shape == mask.shape)
    ii, jj, vv = ssp.find(mask)
    return (ssp.csr_matrix((A[(ii, jj)], vstack((ii, jj))), A.shape))


def EncodeList(input, codebook, vals = None):
    '''return[i] = val[codebook==input[i]]

    if vals is not provided then just return the index in codebook.
    input that are not in codebook has value -1
    '''

    if vals is not None:
        check(len(codebook) == len(vals), "codebook and vals mismatch")
    else:
        vals = range(0, len(codebook))

    dict_code = dict(zip(codebook, vals))        
    return([dict_code.get(item, -1) for item in input])

def EncodeArray(input, codebook, vals = None, dtype = None):
    '''return[i] = val[codebook==input[i]]

    same as Encode. deals specifically with numpy arrays output array
    can be specified when vals = -1 (only index is required) if vals is
    a string array, then unfound input have code "#"

    input and codebook will be converted to dtype if provided.
    '''

    input = arr(input)
    codebook = arr(codebook)
    check(codebook.size < 2e9, "codebook too large")

    if dtype is not None:
        input = input.astype(dtype)
        codebook = codebook.astype(dtype)

    if vals is None:
        output = zeros(input.shape, int32, GetOrder(input))
        exc.encode(input, codebook, output)
    else:
        rIndex = zeros(input.shape, int32, GetOrder(input))
        exc.encode(input, codebook, rIndex)

        unfound = rIndex < 0
        if unfound.any():
            rIndex[unfound] = 0
            output = vals[rIndex]
            
            if vals.dtype.char == 'S':
                output[unfound] = "#"
            else:
                output[unfound] = nan
        else:
            output = vals[rIndex]

    return(output)

def kth(X, k):
    '''get the kth smallest element for each row of X
    '''

    return exc.kth(X, int(k))

def arguniqueInt(input):
    '''get the unique values indeces in vector A. this
    version uses hash_set. result is not sorted.
    '''

    input = arr(input).ravel()
    return exc.argunique(input)

def UniqueInt(input):
    '''get the unique values and their indeces in vector A. this
    version uses hash_set.
    '''

    ui = arguniqueInt(input)
    return sort(input[ui])

def accumarray(subs, val, base, func = 0):
    '''mimic matlab accumarray

    subs: each column is a index vector for a dimension
    val: value vector
    shape: desired shape
    func: 0 for sum, 1 for prod, 2 for max, 3 for min
    '''

    subs = arr(subs)
    val = arr(val)
    sparse  =  issparse(base)

    # check(IsCont(subs) and IsCont(val), 'input must be continguous')

    # handling scalar values
    if val.ndim == 0:
        if subs.ndim == 1: #vector
            val = val*ones(subs.size, dtype = base.dtype)
        else:
            val = val*ones(subs.shape[1], dtype = base.dtype)

    if not sparse:
        if subs.ndim == 1: #vector
            check(base.ndim == 1, 'base should be 1 dimensional')
            check(base.size > subs.max(), "base too small")

            exc.accumvector(subs, val, base, func)
        else: #matrix, turn into vector
            check(base.ndim == 2, 'base  should be 2 dimensional')
            check(arr(shape) > subs.max(1), "shape too small")
                
            exc.accumvector(sub2ind(base, subs[0,:], subs[1,:]), 
                            val, base.ravel(), func)
    else:
        if subs.size == 0:
            return base

        check(func == 0, "func can only be sum for sparse")

        if subs.ndim == 1:#if vector
            base = base + ssp.csr_matrix((val, (zeros(subs.size), subs)), shape = base.shape)
        else:
            base = base + ssp.csr_matrix((val, (subs[0,:], subs[1,:])), shape = base.shape)

    return base

def GroupList(pos, val, n):
    '''group val according to their pos
    
    n: max pos
    '''

    check(max(pos) < n, "n too small")
    result = [[] for i in range(n)]
    for i in range(len(val)):
        result[pos[i]].append(val[i])
    
    return result

def GroupArray(pos, val, n):
    '''group val according to their pos
    
    n: max pos
    '''

    pos = arr(pos)
    val = arr(val)
    check(n > pos.max(), "n too small")
    return(exc.group(pos, val, n))

def issorted(A, ascend = True):
    A = arr(A)
    if ascend:
        return((diff(A) >= 0).all())
    else:
        return((diff(A) <= 0).all())

def Normalize(A, method = 'n1', dim = "col"):
    '''normalize each columns/rows of A so that:
    method = '01': each column's range is [0, 1]
    method = '+-1': each column's range is [-1, 1]
    method's1': each column in A sums to 1
    method'm0': each column has zero mean
    method'v1': each column has variance 1
    method'n1': each column has L2 norm 1
    method'm0v1': each column has 0 mean and 1 variance
    
    return (C, (M, S)) where
    C: result
    M: scaling factor
    S: shifting factor

    shift first, scale second.
    one dim arrays are treated as row vectors
    '''

    if A.ndim == 1: A = row(A)

    C = A.copy()
    M = None
    S = None
    if dim == "col": dim = 0
    elif dim == "row": dim = 1
    else: raise ValueError("unknown dim")

    if istuple(method) or islist(method): 
        M, S = method
    else:

        method = method.lower()
        if method == '01':
            M = -A.min(dim)
            S = 1.0/(A.max(dim) + M)
        if method == '+-1':
            ma = A.max(dim)
            mi = A.min(dim)
            M = -0.5*(mi + ma)
            S = 2.0/(ma - mi)
        elif method=='s1':
            S = 1.0/A.sum(dim)
        elif method=='m0':
            M = -A.mean(dim)
        elif method=='v1':
            S = 1.0/A.std(dim, ddof = 1)
        elif method=='n1':
            S = 1.0/sqrt(sos(A, dim))
        elif method=='m0v1':
            M = -A.mean(dim)
            S = 1.0/A.std(dim, ddof = 1)

    if M is not None: C = shift(C, M, dim)
    if S is not None: C = scale(C, S, dim)
    return (C, (M, S))

def RI(n, size, replace = False, dtype = int32):
    '''return some random indeces
    '''

    n = int(n)
    size = int(size)

    if n == 1:
        return random.randint(0, size)

    if not replace:
        if n >= size: 
            return arange(size, dtype = dtype)
        else: 
            return sort(random.permutation(size)[:n].astype(dtype))
    else:
        return sort(floor(rand(n)*size).astype(dtype))

def AND(arrays, a2 = None):
    '''np.logical_and
    '''

    if a2 is None:
        return reduce(np.logical_and, arrays)
    else:
        return np.logical_and(arrays, a2)

def OR(arrays, a2 = None):
    '''np.logical_or
    '''

    if a2 is None:
        return reduce(np.logical_or, arrays)
    else:
        return np.logical_or(arrays, a2)

def NOT(array):
    '''np.logical_not
    '''

    return np.logical_not(array)

def XOR(a1, a2):
    '''np.logical_xor
    '''

    return np.logical_xor(a1, a2)

def I2L(idx, length = None):
    '''convert number index into logical index
    '''

    if length is None: length = idx.max() + 1
    lidx = zeros(length, dtype = np.bool)
    lidx[idx] = True
    return lidx

def L2I(idx):
    '''convert logical index into number index
    '''

    return find(idx)

def Entropy(p):
    '''compute the entropy
    '''

    p = arr(p)
    p = p[p > 0]
    check(eq(p.sum(), 1, 1e-5), 'wrong distribution')
    
    return -((p*log2(p)).sum())

def MeshGrid(xs, ys):
    '''immitate matlab's meshgrid to generate a 2d mesh
    '''

    xs = arr(xs)
    ys = arr(ys)
    X = repmat(xs, (ys.size, 1))
    Y = repmat(col(ys), (1, xs.size))

    return (X, Y)

def MinMax(arr):
    return (min(arr), max(arr))

def L2Dist(A, B, sq = True):
    '''compute the distance between points in A and in B.
    A: M x d
    B: N X d
    result is the M x N distance matrix
    '''

    if A.ndim != 2 or B.ndim != 2:
        raise ValueError('2D matrices required')

    AA = sos(A, 1)
    BB = sos(B, 1)
    AB = mul(A, B.T)

    D = -2*AB + col(AA) + BB

    if sq:
        D[D < 0] = 0;
        return sqrt(D);
    else:
        return D

if __name__ == '__main__':
    InitLog()

    tic()
    time.sleep(0.5)
    test(eq(toc(msg = "Test", show = False), 0.5, 0.05), "tic/toc")

    A = ones((2,3))
    B = ones((2,2))
    S = spdiag([0,1])
    
    test(isarray(A), "isarray")
    test(ismatrix(matrix(A)), "ismatrix")
    test(issparse(ssp.csr_matrix(A)), "issparse")

    # computation
    emul(B,S)
    mul(B,A)
    ok = False
    try: emul(A,S)
    except ValueError: ok = True
    test(ok, "emul")
    ok = False
    try: mul(A,B)
    except ValueError: ok = True
    test(ok, "mul")

    test(GetOrder(A) == 'C', "GetOrder")

    # sparse
    S = spdiag([0,1])
    test(all(S.diagonal()==[0,1]), "spdiag")

    BS = spmask(B, S)
    test(BS.sum()==1 and BS[1,1]==1, "spmask")

    # index
    A = ones((2,3))
    B = ones((2,2))
    ind = sub2ind(A, [0,1], [0,1], 'c')
    test(ind==[0,4], "sub2ind c")
    ind = sub2ind(A, [0,1], [0,1], 'f')
    test(all(ind==[0,3]), "sub2ind f")
    I,J = ind2sub(A, [0,4], 'c')
    test(all(I==[0,1]) and all(J==[0,1]), "ind2sub c")
    I,J = ind2sub(A, [0,3], 'f')
    test(all(I==[0,1]) and all(J==[0,1]), "ind2sub f")

    test(AssembleVector([{'a': [1,2]}, {'a': [3,4]}], 'a') == 
            arr([1,2,3,4]), "AssembleVector")
    test(AssembleMatrix([{'a': [[1],[2]]}, {'a': [[3],[4]]}], 'a', 'col') == 
            arr([[1,3],[2,4]]), "AssembleMatrix")

    test(emin((arr([1,2,3]),arr([3,1,2]),arr([2,3,1]))) == arr([1,1,1]),'emin')
    test(emax((arr([1,2,3]),arr([3,1,2]),arr([2,3,1]))) == arr([3,3,3]),'emax')

    test(AND((arr([1,0,0]),arr([1,0,1]),arr([1,1,0]))) == arr([True,False,False]),'AND')
    test(OR(arr([1,0,1]),arr([0,1,1])) == arr([True,True,True]),'OR')
    test(NOT(arr([1,0])) == arr([False, True]),'NOT')
    test(XOR(arr([1,0,1]),arr([1,0,0])) == arr([False, False, True]),'XOR')

    # encoders
    A = arr([0,0,1,2,1,3])
    B = arr([2,1,0])
    O = ones(6, dtype = float32)
    Z = zeros(6, dtype = int)
    S = arange(0,6)

    ue = UniqueInt(A) 
    ue.sort()
    test(ue == arr([0,1,2,3]), "uniqueInt")

    enc = EncodeList(["ha",1,"ha","ho",0],["ha","ho",1],[0,1,"pu"])
    test(enc == [0, "pu", 0, 1, -1], "encode list")

    enc = EncodeArray(A, B)
    test(enc == arr([2,2,1,0,1,-1]), "encode index")
    enc = EncodeArray(A, B, arr(["a","b","cd"]))
    test(enc == arr(["cd","cd","b","a","b","#"]),
            "encode value")

    g = GroupArray(int32(A), int32(S), A.max() + 1)
    test(len(g) == A.max() + 1 and (g[1] == arr([2,4])).all(), 
            "GroupArray")
    
    g = GroupList(A, S, A.max() + 1)
    test(len(g) == A.max() + 1 and g[1] == [2,4], 
            "GroupList")

    L = [l % 5 for l in range(int(1e5))]
    U = range(5)
    tic();EncodeList(L, U);toc(msg = "EncodeList")
    tic();EncodeArray(L, U);toc(msg = "EncodeArray")

    tic();GroupList(L, L, max(L) + 1);toc(msg = "GroupList")
    tic();GroupArray(int32(L), int32(L), max(L) + 1);toc(msg = "GroupArray")
        
    subs = int32(A)
    tmp = accumarray(subs, 1, zeros(4))
    test(tmp == arr([2,2,1,1]), "accumarray dense")
    test(accumarray(subs, 1, tmp) == arr([4,4,2,2]), "accumarray accum")
    test(accumarray(subs, 1, ssp.csr_matrix((1, 4))).todense() == 
            arr([2,2,1,1]), "accumarray sparse")

    K1 = arr([3,3,5],dtype = int32)
    K2 = arr([2,5,3],dtype = int32)
    test(issorted(K1) == True and issorted(K2) == False, "issorted")

    test(Normalize(arr([[1,2,3],[4,5,6]]), 'm0v1', 'row')[0] ==
            arr([[-1,0,1],[-1,0,1]]), 'Normalize (shift, scale, vec)')

    test(L2Dist(row(arr([1])), col(arr([1,2,3]))) == arr([0,1,2]), 'L2Dist')
