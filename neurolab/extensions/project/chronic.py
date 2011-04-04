from django import forms

import config
from neurolab.db import *
from neurolab.output import *
from neurolab.formats.matlab import MatlabOutputTemplate

class ConcatenatedWaves(MatlabOutputTemplate):
    slug = 'concatenated-waves'
    title = 'Concatenated Waves'
    component_types = ('wave-group',)
    
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
    
    def get_variables(self, entry, jobdata):
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
                    k = 0
                    while k < _tb[1]:
                        inc = min(chunk, _tb[1]-k)
                        _inc, _k = [round(v*sr) for v in (inc, k)]
                        _inc = min(_inc, array.shape[1]-_k)
                        
                        if _k > array.shape[1]:
                            break
                        
                        _l = array.shape[1] if _inc < 0 else _k + _inc
                        array[j, _k:_l] = resample(carray[i, k:k+inc], _inc)
                        
                        k += chunk
                    j += 1
        
        return {'wavedata': array}
    
    def jobs(self, entry):
        cur = 0
        step = entry.criteria['segment_length']
        length = entry.block.length
        
        while cur < length:
            _step = min(step, length-cur)
            yield {'start': cur, 'stop': cur+_step}
            cur += step
    


OutputTemplate.templates.extend(ConcatenatedWaves)