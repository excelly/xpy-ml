from ex.common import *
from common import *
import pyfits as pf

def HDU2Mats(hdu):
    '''process a single hdu.
    '''

    result = {}

    # header
    header = {}
    header_comment = {}
    cl = hdu.header.ascardlist()
    for card in cl:
        header[card.key] = card.value
        header_comment[card.key] = card.comment \
            if len(card.comment) > 1 else []

    result["header"] = header
    result["header_comment"] = header_comment

    # data
    if not hdu.header.has_key('XTENSION'): #primary
        type = 'IMAGE'
    else: #extensions
        type = hdu.header['XTENSION']
    result['type'] = type

    if hdu.data is None:
        result['data'] = []
    else:
        if type == 'IMAGE':
            result['data'] = FixEndian(hdu.data)
        elif type == 'TABLE' or type == 'BINTABLE':
            tbdata = hdu.data
            names = tbdata.names

            data = {}
            for i in range(0, len(names)):
                data[names[i]] = FixEndian(tbdata.field(names[i]))
            result["data"] = data
        else:
            raise ValueException('unknown FITS type')

    return(result)

class FITS:
    '''A wrapper for pyfits. The actual data are stored in HDUs.
    '''
    
    def __init__(self, filename):
        '''Read FITS from file.
        '''
        self.HDUs = pf.open(filename)

    def __del__(self):
        self.Close()

    def Close(self):
        if hasattr(self, 'HDUs'):
            self.HDUs.close()

    def GetMats(self):
        '''transform this FITS to a list of matlab structs.

        use np.array(, dtype = np.object) to turn the result of this
        function into a cell array.
        '''

        return([HDU2Mats(hdu) for hdu in self.HDUs])

    def SaveAsMat(self, filename):
        '''save the current FITS as a .mat file
        '''

        mats = np.array(self.GetMats(), dtype = np.object)
        SaveMat(filename, {"HDUs": mats})
