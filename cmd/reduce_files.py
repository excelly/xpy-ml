from ex import *
import ex.pp.mr as mr

def usage():
    print('''
map files using specified handler

python reduce_files.py --module={module path string} --input=input_files(wildcard) [--output={output directory}] [--poolsize={number of parallel processes}]

--module: the processing module. this module should contain a Reducer class with functions:
GetKey(filename): group files together. 
__init__(output_dest):  for the output_directory.
Reduce(): process one group of files, return the number of files processed
Aggregate(): report a number, usually the number of files processed in total.
''')
    sys.exit(1)

if __name__ == '__main__':
    InitLog()
    opts=CmdArgs(sys.argv[1:], ['module=','output=','input=', 'poolsize=' 'help'], usage)

    output_dir=os.path.abspath(opts.get('--output', os.getcwd()))
    input_files=ExpandWildcard(opts['--input'])
    poolsize=int(opts.get('--poolsize', 1))
    module_name=opts['--module']

    exec "from {0} import Reducer".format(module_name)
    log.info('Reducing {0} files using module "{1}"'.format(
            len(input_files), module_name))

    reducer=Reducer(output_dest=output_dir)
    engine=mr.ReduceEngine(reducer, poolsize)

    keys=[reducer.GetKey(f) for f in input_files]
    jobs=zip(keys, input_files)
    points=engine.Start(jobs)
    log.info('{0} points gained'.format(points))
