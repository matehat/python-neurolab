from django import forms
from neurolab.db import *
from neurolab.db.models import Component
from neurolab.tasks.models import ProcessingTask
from neurolab.utils import metadata
from neurolab.graphics.base import *

class Wave(Component):
    slug = 'wave'
    name = 'Wave'
    sampling_rate = FloatField(required=True)
    metakeys = metadata('metadata')
    
    @metakeys.item
    def step(self):
        with self.array('r') as data:
            return int(data.shape[0] // 1e6) or 1
    
    @metakeys.item
    def maximum(self):
        from numpy import max
        with self.array('r') as data:
            return float(max(data[::self.step]))
    
    @metakeys.item
    def minimum(self):
        from numpy import min
        with self.array('r') as data:
            return float(min(data[::self.step]))
    
    
    @property
    def dataset_shape(self):
        return (self.size,)
    
    
    class CriteriaForm(forms.Form):
        name = forms.CharField(label="Name", required=True)
        sampling_rate = forms.FloatField(label="Sampling Rate", required=True)
    
    Grapher = WaveGrapher

class Wavegroup(Component):
    slug = 'wave-group'
    name = 'Wave Group'
    
    count = IntField(min_value=1, required=True)
    sampling_rate = FloatField(required=True)
    metakeys = metadata('metadata')
    
    @metakeys.item
    def step(self):
        with self.array('r') as data:
            return int(data.shape[1] // 1e6) or 1
    
    @metakeys.item
    def maxima(self):
        from numpy import max
        with self.array('r') as data:
            return [float(m) 
                for m in list(max(data[:, ::self.step], 1))]
    
    @metakeys.item
    def minima(self):
        from numpy import min
        with self.array('r') as data:
            return [float(m) 
                for m in list(min(data[:, ::self.step], 1))]
    
    
    @property
    def dataset_shape(self):
        return (self.count, self.size,)
    
    
    class CriteriaForm(forms.Form):
        name = forms.CharField(label="Name", required=True)
        count = forms.IntegerField(label="Wave Count", required=False, min_value=1)
        sampling_rate = forms.FloatField(label="Sampling Rate", required=True)
    
    Grapher = WaveGroupGrapher

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
    


Component.registry.extend(Wave, Wavegroup)
ProcessingTask.tasks.extend(Resample)