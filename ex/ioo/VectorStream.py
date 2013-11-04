from ex.common import *
from common import *

pickle_proto=2
type_dict={"list":1, "array":2}

class VectorOutputStream:
    '''Output a sequence of vectors to a pickle file
    '''

    def __init__(self, output_stream, name="", type="array"):
        '''Constructor.
        
        output_stream: the opened pickle file
        name: name of this stream
        type: type of this stream. "list" or "array"
        no_header: do not write the header for this stream
        '''

        self.output=output_stream
        self.name=name
        self.type=type_dict[type]

        pickle.dump(output, (name, type), pickle_proto)

    def Write(self, v):
        '''output a vector
        '''

        if self.type == 1: 
            check(isinstance(v, list), "wrong type. should be a list")
        elif self.type == 2: 
            check(isarray(v), "wrong type. should be a numpy array")
            check(v.ndim == 1, "only 1D vector allowed")
        else:
            raise ValueError("wrong type initialized")

        pickle.dump(self.output, v, pickle_proto)

class VectorInputStream:
    '''Read a consecutive vector stream from a sequence of pickled
    vectors.

    The vector could be a list or a numpy array.
    '''

    def __init__(self, input_stream, chunk_length=int(1e7)):
        '''Constructor.

        input_stream: the opened pickle file
        chunk_length: length of the vector returned each time

        This instance will seek to the start of the file
        '''

        self.input=input_stream
        self.chunk_length=int(chunk_length)
        self.Reset()

    def Reset(self):
        '''Reset the current stream. read in header info
        '''

        self.input.seek(0)
        self.name, self.type=pickle.load(self.input)
        self.type=type_dict[self.type]
        self.remainder=[]

    def Read(self):
        '''Read a vector out of the stream
        '''

        remained=len(self.remainder)
        
        #if the remainder is enough
        if remained >= self.chunk_length: 
            result=self.remainder[0:self.chunk_length]
            self.remainder=self.remainder[self.chunk_length:]
            return(result)

        # read more data
        if self.type == 1:#list
            result=self.remainder

            try:
                while len(result) < self.chunk_length:
                    result.extend(pickle.load(self.input))
            except EOFError: pass

            if len(result) > self.chunk_length:
                self.remainder=result[self.chunk_length:]
                result=result[0:self.chunk_length]
            else:
                self.remainder=[]
        elif type == 2: #numpy array
            result=empty(self.chunk_length, dtype=float64)
            result[0:remained]=self.remainder
            
            try:
                while remained < self.chunk_length:
                    new=pickle.load(self.input)
                    if remained + new.size < self.chunk_length:
                        result[remained:(remained + new.size)]=new
                    else:
                        result[remained:self.chunk_length]=new[0:(self.chunk_length - remained)]
                        self.remainder=new[(self.chunk_length - remained):]
                    remained=remained + new.size
            except EOFError: pass

            if remained < self.chunk_length:
                result=result[0:remained]
        else:
            raise ValueError("wrong type initialized")

        return(result)

    def next(self):
        o=self.read()
        if len(o) == 0: raise StopIteration()
        return(o)

    def __iter__(self):
        return(self)

if __name__ == '__main__':
    pass
