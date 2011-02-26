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
    
    def filedata(self):
        matfile = self.matfile()
        return {'channels': dict([(k, {}) for k in matfile.keys()])}
        del matfile
    
    def read_dataset(self, channels, starttime=0, endtime=None):
        matfile = self.matfile()
        for k in matfile:
            if k not in channels:
                del matfile[k]
        
        dataset = {}
        for channel in channels:
            dataset[channel] = matfile[k][slice(starttime, endtime)]
        del matfile
        return dataset
    
    def write_dataset(self, channels):
        data = self.matfile()
        data.update(channels)
        self.sourcefile.mkdirs()
        savemat(self.sourcefile.fullpath, data)
    

def register_formats(formats):
    formats.extend(MatlabFormat)
