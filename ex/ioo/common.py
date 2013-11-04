from ex.common import *
import gzip
import bz2
import glob
import cPickle as pickle
import struct
import socket
import sqlite3 as sql
import scipy.io as sio

pickle_proto=2

def ExpandWildcard(pattern):
    '''expand a file pattern
    '''

    files=glob.glob(os.path.expanduser(pattern));
    log.debug('{0} files expanded from pattern: {1}'.format(
            len(files), pattern))
    return [os.path.abspath(file) for file in files]

def AddExt(filename, ext=""):
    '''Add ext to a filename if it is not there
    '''

    if ext is "": return

    if not ext.startswith('.'): ext="."+ext
    if not filename.endswith(ext): 
        return filename + ext
    else:
        return filename

def FileAge(path):
    '''return the age of the last modification of path in seconds
    '''

    if not os.path.exists(path): return -1
    mtime = os.stat(path).st_mtime
    now = time.mktime(time.localtime())
    return now - mtime

def MakeDir(path):
    '''makedir if target not exists
    '''

    if not os.path.exists(path):
        os.mkdir(path)
        return True
    else:
        log.debug('Dir {0} already exists'.format(path))
        return False

def SplitFilename(path):
    path = os.path.basename(path)
    path = path.split('.')
    return ('.'.join(path[:-1]), path[-1])

def ParseAddr(str):
    '''parse a network address string and return a tuple that can be
    used by socket's connect() or bind()
    '''

    addr=str.split(':') 
    if len(addr) == 1: raise ValueError('port not specified')
    addr[1]=int(addr[1]) 
    return tuple(addr)

class xFile:
    '''A wrapper for file. 

    Support compression. The actual compressor is stored in
    self.target.

    Used to facilitate the 'with' statement
    '''
    
    def __init__(self, filename, mode="r"):
        '''Constructor. receive file info. 

        Not opening the file. Call Open().

        format will be inferred from the filename and can be "gz" or
        "bz" or ""(plain).
        '''

        if filename.lower().endswith(".gz"): format="gz"
        elif filename.lower().endswith(".bz"): format="bz"
        else: format=""

        self.filename=filename
        self.mode=mode
        self.format=format

    def __del__(self):
        '''Destructor
        '''

        self.Close()

    def Open(self):
        '''Open the file.

        Use the info passed to the constructor.
        '''

        if self.format == "gz":
            self.target=gzip.open(self.filename, self.mode, 
                                  compresslevel = 1)
        elif self.format == "bz":
            self.target=bz2.BZ2File(self.filename, self.mode, 10240, 5)
        elif self.format == "":
            self.target=open(self.filename, self.mode)

        return(self.target)

    def Close(self):
        '''Close the file.
        '''

        if hasattr(self, 'target'): self.target.close()

    def Reset(self):
        '''reset the file pointer to the beginning of the file
        '''

        if hasattr(self, 'target'): self.target.seek(0)

    def Remove(self):
        '''remove this file itself
        '''

        self.Close()
        os.remove(self.filename)
        
    def __enter__(self):
        return(self.Open())

    def __exit__(self, type, value, traceback):
        self.Close()
        return(value == None)

def SaveText(filename, text, append=False):
    '''save a string to a text file
    '''

    with xFile(filename, 'a' if append else 'w') as o:
        o.write(text)

class PickleStream:
    '''Extended unpickler that supports iterable interface
    '''

    def __init__(self, input_file):
        '''Constructor. input_file can be the filename or the file
        handle.
        '''

        if isinstance(input_file, str):
            self.xfile=xFile(input_file, 'r')
            self.input=xFile.Open()
        else:
            self.input=input_file

    def __del__(self):
        '''close the stream if own it.
        '''

        if hasattr(self, 'xfile'):
            self.xfile.Close()

    def Reset(self):
        self.input.seek(0)

    def next(self):
        try: o=pickle.load(self.input)
        except EOFError: raise StopIteration
        return o

    def __iter__(self):
        return(self)

def LoadPickles(filename):
    '''load objects from a pickle file.
    '''

    with xFile(filename, 'rb') as input:
        result=[o for o in PickleStream(input)]
    
    if len(result) == 1: result=result[0]
    return(result)

def SavePickles(filename, objects, append=False):
    '''save a list of objects to a pickle file.

    filename: name of the pickle file.  
    objects: list of objects to save. note that if objects is
    iterable then it will be unpacked and saved to file one by
    one. so use [objects] if you want to save them as a whole.
    format: format of the pickle file.
    '''

    with xFile(filename, 'ab' if append else 'wb') as output:
        for o in objects:
            pickle.dump(o, output, pickle_proto)

def SavePickle(filename, object, append=False):
    '''save a single object into pickle
    '''

    SavePickles(filename, [object], append)

def SendPickle(sock, obj):
    '''send an object through socket, sync op
    '''

    data=pickle.dumps(obj, pickle_proto)
    l=struct.pack('Q', len(data))
    data=l + data

    sock.sendall(data)

    return len(data) - len(l)

def SendPickle(dest, obj):
    '''send an object to the dest server, sync op
    '''

    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(eu.ParseAddr(dest))
    data_sent=self.SendPickle(sock, obj)
    sock.close()
    return data_sent

def ReceivePickle(sock):
    '''receive an object from socket, sync op
    '''

    l=sock.recv(8)
    if len(l) < 8: raise RuntimeError('invalid pickle received')
    l=struct.unpack('Q', l)[0]
    
    data=sock.recv(l)
    while len(data) < l:
        data=data + sock.recv(l - len(data))
        
    return pickle.loads(data)

def FixEndian(a, endian = '<'):
    if a.dtype.str[0] != endian:
        return a.astype(endian + a.dtype.str[1:])
    else:
        return a

def SaveMat(filename, objs, compress=True, oned_as='column'):
    '''save a mat file. objs is the dictionary of variables
    '''

    if not filename.endswith('.mat'):
        filename += '.mat'

    return sio.savemat(filename, objs, do_compression=compress, oned_as=oned_as)

def LoadMat(filename, chars_as_strings=False, struct_as_record=True):
    '''load a mat file
    '''

    return sio.loadmat(filename, chars_as_strings=chars_as_strings, struct_as_record=struct_as_record)

def GetDB(filename, cache_size=None):
    '''get a db connection
    the unit for cache_size is megabytes
    '''

    db=sql.connect(filename)
    if cache_size is not None:
        db.execute('pragma cache_size={0}'.format(
                cache_size*1024))
    return db

def ReadMatrixTxt(filename, splitter, dtype=np.float64, has_header=False):
    '''read a numeric matrix from a text file
    the text file should have a header
    '''

    with open(filename) as f:
        if has_header:
            header=f.readline().rstrip('\n').split(splitter)
            log.info('Data Header: \n{0}'.format(header))
        else:
            header=None
        rows=f.readlines()

    data=empty((len(rows), len(rows[0].split(splitter))), 
               dtype=dtype)

    for i in range(len(rows)):
        if len(rows[i].strip()) > 0:
            data[i]=rows[i].split(splitter)

    log.info('Read {0} data matrix'.format(data.shape))

    return (header, data)

if __name__ == '__main__':
    pass
