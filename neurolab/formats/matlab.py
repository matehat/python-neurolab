from os.path import exists
from neurolab.formats.base import BaseFormat
from scipy.io import loadmat, savemat

class MatlabFormat(BaseFormat):
    slug = 'matlab'
    writable = True
    
    def matfile(self):
        try:
            return loadmat(self.sourcefile.fullpath)
        except:
            return {}
    
    def metadata(self):
        matfile = self.matfile()
        return {'waves': dict([(k, {}) for k in matfile.keys()])}
        del matfile
    
    def read_dataset(self, waves, starttime=0, endtime=None):
        matfile = self.matfile()
        for k in matfile:
            if k not in waves:
                del matfile[k]
        
        dataset = {}
        for channel in waves:
            dataset[channel] = matfile[k][slice(starttime, endtime)]
        del matfile
        return dataset
    
    def write_dataset(self, waves):
        data = self.matfile()
        data.update(waves)
        self.sourcefile.mkdirs()
        savemat(self.sourcefile.fullpath, data)
    

def register_formats(formats):
    formats.extend(MatlabFormat)
