from neurolab.db import *
from neurolab.output.models import *

class TextOutputTemplate(FileOutputTemplate):
    def make_filename(self, entry, jobdata):
        return "%s.txt" % self.make_filetitle(entry, jobdata)
    
    def write_file(self, entry, jobdata, fname):
        import numpy
        numpy.savetxt(fname, self.get_variables(entry, jobdata))
    
