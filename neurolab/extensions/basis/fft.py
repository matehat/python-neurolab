from django import forms

import config
from neurolab.tasks.models import ProcessingTask, TaskJob
from neurolab.db.models import SourceFile, Datasource

class WaveProcessingTask(ProcessingTask):
    argument_types = ('wave', 'wave-group')

class Resample(WaveProcessingTask):
    name = 'Wave Resampling'
    slug = 'resample-wave'
    
    class CriteriaForm(forms.Form):
        sampling_rate = forms.FloatField(label='Sampling Rate', required=True)
    
    
    def create_component(self, name):
        arg = self.argument
        cls = type(arg)
        result = self.result = cls(
            block=arg.block,
            parent=arg, 
            name=name,
        )
        for prop in ('dtype', 'count'):
            if hasattr(arg, prop):
                setattr(result, prop, getattr(arg, prop))
        result.sampling_rate = self.criteria['sampling_rate']
        result.size = (arg.size / arg.sampling_rate) * result.sampling_rate
        result.save()
    
    def chunks(self, inp):
        factor = self.argument.sampling_rate / self.result.sampling_rate
        chunksize = config.CHUNKSIZES['fft']
        
        def _chunks(t_len):
            cur = 0
            while cur*factor < t_len:
                L = min([factor*chunksize, t_len-cur*factor])
                l = int(L/factor)
                yield slice(cur*factor, cur*factor+L), slice(cur, cur+l), l
                cur += chunksize
        
        if self.argument.slug == 'wave-group':
            for i in range(self.argument.count):
                for _islice, _oslice, l in _chunks(inp.shape[1]):
                    yield (i, _oslice), (i, _islice), l
        else:
            for _islice, _oslice, l in _chunks(inp.shape[0]):
                yield (_oslice,), (_islice,), l
    
    def handle_job(self, *args, **kwargs):
        from scipy.signal import resample
        
        inp = self.argument.array('r')
        outp = self.result.array('w')
        
        for _o, _i, l in self.chunks(inp):
            outp[_o] = resample(inp[_i], l)
        
        inp.close()
        outp.close()
        self.result.done()
    


class FFT(WaveProcessingTask):
    name = 'Fast-Fourier Transform'
    slug = 'fft'
    
    class CriteriaForm(forms.Form):
        n = forms.IntegerField(label='Length of Fourier Transform', required=False)
    


ProcessingTask.tasks.extend(Resample, FFT)