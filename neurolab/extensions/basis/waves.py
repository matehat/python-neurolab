from django import forms
from neurolab.db import *
from neurolab.db.models import Component
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


Component.registry.extend(Wave, Wavegroup)