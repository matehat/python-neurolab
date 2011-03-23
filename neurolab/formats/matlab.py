from neurolab.db import *
from neurolab.output.models import *

class MatlabOutputTemplate(FileOutputTemplate):
    def make_filename(self, entry, jobdata):
        return "%s.mat" % self.make_filetitle(entry, jobdata)
    
    def write_file(self, entry, jobdata, fname):
        from scipy.io import savemat
        savemat(fname, self.get_variables(entry, jobdata))
    
