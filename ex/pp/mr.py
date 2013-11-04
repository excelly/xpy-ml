from ex.common import *
from ex.ioo.common import *
from ex.pp.common import *

# NOTE: one copy of mapper/reducer will be held in each process, so
# the data replication is lower than using multiprocessing.Pool. But
# here the data within the mapper/reducer should be readonly.

_mapper = None
_reducer = None
def _init_mapper(args):
    global _mapper; _mapper = args
def _init_reducer(args):
    global _reducer; _reducer = args

def DoMapJob(job):
    '''process a single map job. each jobs_spec is a tuple (engine,
    (key, val)). (key, val) will be passed to the mapper
    directly.the mapper should return a list of result (key, val).
    '''

    key, val=job
    results=_mapper.Map(key, val)
    log.debug('{0} mapped the job {1}. {2} results returned.'.format(
            _mapper.name, job, len(results)))

    return results # a list of (key, val) for the reducer

def DoReduceJob(job):
    '''process a reduce single job. a job_spec is a tuple (engine,
    job). the job should be a tuple (key, vals), which will be passed
    to one Reduce() function.

    returns the (key, result) pair.
    '''

    key, vals=job
    result=_reducer.Reduce(key, vals)

    log.debug('{0} reduced the key {1}'.format(_reducer.name, key))

    return (key, result)

class MapEngine:
    '''A class that handles Mapping jobs.
    '''

    def __init__(self, mapper, pool_size):
        '''mapper: the mapper for the data. see the BaseMapper below.

        pool_size: number of processes to use.
        '''

        self.mapper=mapper
        self.pool_size=int(pool_size)
        mapper.engine=self

        log.info('MapEngine initialized: Mapper={0}'.format(self.mapper.name))

    def Start(self, jobs):
        '''start processing jobs. jobs should be a list of (key, val)
        pairs. each job will be dispatched to a map function. if each
        jobs is just a scalar, then the keys {0,1,...,n} will be assigned.

        returns the a of all the result (key, val)
        '''

        log.info('Start mapping {0} jobs using {1} processes'.format(
                len(jobs), self.pool_size))

        if not istuple(jobs[0]):
            jobs=enumerate(jobs)

        results=ProcJobs(DoMapJob, jobs, self.pool_size, _init_mapper, self.mapper)

        results=Flatten(results)
        log.debug('{0} results returned'.format(len(results)))

        return results

class ReduceEngine:
    '''handles the reducing jobs. the memory assumption is that the
    results for keys can be held.
    '''
    
    def __init__(self, reducer, pool_size):
        '''ReduceEngine
        pool_size: number of parallel processes
        '''

        self.reducer=reducer
        self.pool_size=int(pool_size)
        reducer.engine=self

        log.info('ReduceEngine initialized: Reducer={0}'.format(self.reducer.name))

    def Start(self, jobs):
        '''start processing jobs

        jobs should be a list of (key, val). these jobs will then be
        grouped according to key and send to the Reducer. all the vals
        of one key is handled by one reducer. if each jobs is just a
        scalar, then the keys {0,1,...,n} will be assigned.

        returns the list of results from each reducer. if the Reducer
        specifies do_aggregation, then returns the result of reducer's
        Aggregate().
        '''

        if not istuple(jobs[0]):
            keys=range(len(jobs))
            jobs=[(i, [jobs[i]]) for i in range(len(jobs))]
        else:
            keys, vals=zip(*jobs)
            jobs=Group(keys, vals)

        log.info('Reducing {0} jobs / {1} keys with {2} processes'.format(
                len(keys), len(jobs), self.pool_size))

        outputs=ProcJobs(DoReduceJob, jobs, self.pool_size, _init_reducer, self.reducer)
        
        if self.reducer.do_aggregation:
            outputs=self.reducer.Aggregate(outputs)

        return outputs

class PartitionEngine:
    '''handles the partitioning job
    '''

    def __init__(self, pool_size=1):
        '''pool_size: number of processes used for
        partitioning. currently only 1 process can be used. further
        the result will not be compressed.
        '''

        if int(pool_size) > 1: 
            log.warn('Parallel partitioning using not supported yet')

        self.pool_size=1;

    def Partition(self, input_files, output_dir, output_prefix='', batch_size=1):
        '''read input_files, output records with the same key into the
        same file in output_dir. the files are named as
        'output_prefix_key.mrf'. prefix are used so that reducers can
        recognize them.

        the input_files should be pickle files that stores (key, val)
        pairs.

        batch_size: how many files to reading before each output. note
        that it should be small enough so that the files can be fit
        into memory.
        '''

        n=len(input_files)
        log.info('Partition {0} files to {1}'.format(n, output_dir))

        if len(output_prefix) > 0 and not output_prefix.endswith('_'): 
            output_prefix += '_'

        start=0
        while start <= len(input_files): # for each batch
            end=min(n, start + batch)
            files=input_files[start:end]

            output_buffer={}
            for f in files: # for each file
                ps=PickleStream(f)
                for p in ps:
                    key=p[0]
                    if output_buffer.has_key(key):
                        output_buffer[key].append(p)
                    else:
                        output_buffer[key]=[p]

            for key, ps in output_buffer.items(): # output the buffer
                SavePickles("{0}/{1}{2}.mrf".format(
                        output_dir, output_prefix, key), ps, append=True)

            start=end

class BaseMapper:
    '''A class that handles Mapping jobs
    Need to specify the Map() function
    '''
    
    def __init__(self, name, output_dest = None):
        '''initialize the mapper. the mapper should have a
        name. output_dir specifies the folder to output map
        results. this class can also hold global parameters that are
        used by the Map() function.

        usually the output_dest is specified so that the mapper knows where to store the results.
        '''

        self.name=name
        self.output_dest=output_dest

        log.debug('Mapper {0} initialized. Output={1}'.format(
                name, output_dest))

    def Map(self, key, val):
        '''an example Map() function.

        input: this function accept a key and the value to
        process. the val is a tuple that can contain anything.

        output: this function should return the resulting list of
        tuples (key, value).
        '''

        input_file=key
        params=val

        # output to files
        output_file="{0}/{1}_mapped.pkl".format(
            self.output_dest, input_file)
        SavePickles(output_file, [(key, val)])
        
        # output to server via socket
        SendPickle(self.output_dest, [(key, val)])

        # direct return
        return (key, val)

class BaseReducer:
    '''A class that handles Reducing jobs. the Reduce function handles
    all the data related to one key.
    '''
    
    def __init__(self, name, do_aggregation=False):
        '''initialize the reducer. 
        '''

        self.name=name
        self.do_aggregation=do_aggregation

    def Reduce(self, key, vals):
        '''an example Reduce() function.

        input: this function accept a key and a list of record for
        this key. for example, the key can be the subtask name, and
        the vals can be the list of files for this subtask. 

        output: this function should return a result object. 
        '''

        return ",".join(vals)

    def Aggregate(self, pairs):
        '''aggregate the results from different keys together
        '''

        keys, results=unzip(pairs)
        return "\n".join(results)
