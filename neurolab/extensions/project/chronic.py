from django import forms

import config
from neurolab.db import *
from neurolab.output import *
from neurolab.formats.matlab import MatlabOutputTemplate
from neurolab.formats.text import LabChartTextOutputTemplate

class ConcatenatedWaves(object):
    class CriteriaForm(forms.Form):
        segment_length = forms.FloatField(label="Segment length (s):")
        sampling_rate = forms.FloatField(label="Sampling rate (Hz):")
        references = forms.CharField(
            label="References:",
            help_text="Lines of the form \"[wavename]: [index],[index],[index]\"",
            widget=forms.Textarea
        )
    
    
    def make_filetitle(self, entry, jobdata):
        return "%s_%.2f-%.2f" % (self.name, jobdata['start'], jobdata['stop'])
    
    def get_array(self, entry, jobdata):
        import numpy as np
        from scipy.signal import resample
        
        num = 0
        components = []
        block = entry.block
        tb = jobdata['start'], jobdata['stop']
        T = (tb[1] - tb[0])*entry.criteria['sampling_rate']
        
        try:
            for ref in filter(None, entry.criteria['references'].split("\n")):
                k, indices = [s.strip() for s in ref.split(":")]
                indices = [int(i.strip()) for i in indices.split(",")]
                num += len(indices)
                components.append((Component.objects.get(block=block, name=k), indices))
        except Component.DoesNotExist:
            raise TypeError("Provided component name does not exist [%s]" % k)
        except ValueError:
            raise TypeError("Provided references do not comply to the needed format")
        
        chunk = config.CHUNKSIZES['fft']
        array = np.zeros((num, T))
        j = 0
        
        for cmp, indices in components:
            sampl = cmp.sampling_rate
            _tb = [v*sampl for v in tb]
            sr = entry.criteria['sampling_rate']/sampl
            with cmp.array('r') as carray:
                for i in indices:
                    k = _k = 0
                    while k < _tb[1]:
                        inc = min(chunk, _tb[1]-k)
                        _inc = min(np.floor(inc*sr), array.shape[1]-_k)
                        
                        if _k > array.shape[1]:
                            break
                        
                        _l = array.shape[1] if _inc < 0 else _k + _inc
                        
                        try:
                            array[j, _k:_l] = A = resample(carray[i, k:k+inc], int(_l-_k))
                        except ValueError:
                            if _inc == 0:
                                break
                        
                        k += chunk
                        _k = _l
                    j += 1
        
        print "Finished getting output variables"
        return array
    
    def jobs(self, entry):
        cur = 0
        step = entry.criteria['segment_length']
        length = entry.block.length
        
        while cur < length:
            _step = min(step, length-cur)
            yield {'start': cur, 'stop': cur+_step}
            cur += step
    

class MatlabConcatenatedWaves(ConcatenatedWaves, MatlabOutputTemplate):
    slug = 'concatenated-waves-matlab'
    title = 'Concatenate Waves to .mat Format'
    component_types = ('wave-group',)

class LabchartTextConcatenatedWaves(ConcatenatedWaves, LabChartTextOutputTemplate):
    slug = 'labchart-concatenated-waves-txt'
    title = 'Concatenate Waves to Labchart Text Format'
    component_types = ('wave-group',)
    
    def get_array(self, entry, jobdata):
        return super(LabchartTextConcatenatedWaves, self).get_array(entry, jobdata).transpose()
    


OutputTemplate.templates.extend(MatlabConcatenatedWaves, LabchartTextConcatenatedWaves)
