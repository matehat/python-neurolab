from neurolab.db import *
from neurolab.output.models import *

class TextOutputTemplate(FileOutputTemplate):
    def make_filename(self, entry, jobdata):
        return "%s.txt" % self.make_filetitle(entry, jobdata)
    
    def write_file(self, entry, jobdata, fname):
        import numpy
        numpy.savetxt(fname, self.get_array(entry, jobdata))
    

class LabChartTextOutputTemplate(TextOutputTemplate):
    def write_file(self, entry, jobdata, fname):
        import numpy 
        numpy.savetxt(fname, self.get_array(entry, jobdata), fmt="   %.16e", delimiter="\t", newline="\t\n")
    
