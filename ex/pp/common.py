from ex import *

import multiprocessing as mp

def NumCPU():
    return mp.cpu_count

def SeedRand(extra = 0):
    run_id = int(os.getpid() + time.time() + extra)
    random.seed(run_id)

def ProcJobs(func, jobs, nproc, global_init = None, global_data = None, chunk_size = None):
    '''process jobs in parallel
    '''

    if nproc > 1:
        pool = mp.Pool(nproc, global_init, (global_data,))
        result = pool.map(func, jobs, chunk_size)
        pool.close()
        return result
    else:
        if global_init is not None:
            global_init(global_data)
        return [func(job) for job in jobs]

def Group(keys, vals):
    '''group vals according to keys. return a list of tuples. each
    tuple is (key, [vals with this key])
    '''

    pairs = zip(keys, vals)
    pairs = sorted(pairs, key = lambda pair: pair[0])
    keys, vals = unzip(pairs)

    r = []
    n = len(vals)
    start = 0
    while start < n:
        key = keys[start]
        end = start + 1
        while end < n and keys[end] == key:
            end += 1

        r.append((key, vals[start:end]))
        start = end

    return r
