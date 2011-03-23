from django import forms

import config
from neurolab.extensions.basis.fft import WaveProcessingTask, ProcessingTask
from neurolab.db import *
from neurolab.db.models import Component
from neurolab.utils import metadata
from neurolab.graphics.base import Grapher

class TimeFrequencyScalogram(WaveProcessingTask):
    name = 'Time-frequency scalogram'
    slug = 'time-freq-scalogram'
    
    class CriteriaForm(forms.Form):
        time_sampling_rate = forms.FloatField(label='Time Sampling Rate', required=False)
        freq_sampling_rate = forms.FloatField(label='Frequency Sampling Rate', required=True, initial=4)
        freq_start = forms.FloatField(label='First Frequency', required=True, initial=0.25)
        freq_stop = forms.FloatField(label='Last Frequency', required=True, initial=100.0)
    
    def create_component(self, name):
        argument = self.argument
        cls = Scalogram if argument.slug == 'wave' else ScalogramGroup
        
        result = self.result = cls(
            parent=self.argument, 
            block=argument.block,
            name=name,
        )
        for prop in ('dtype', 'count'):
            if hasattr(argument, prop):
                setattr(result, prop, getattr(argument, prop))
        for prop in ('time_sampling_rate', 'freq_sampling_rate', 'freq_start', 'freq_stop'):
            setattr(result, prop, self.criteria[prop])
        result.save()
    
    def chunks(self, inp):
        factor = self.argument.sampling_rate / self.result.time_sampling_rate
        chunksize = config.CHUNKSIZES['fft']
        
        def _chunks(t_len):
            cur = 0
            while cur*factor < t_len:
                L = min([factor*chunksize, t_len-cur*factor])
                l = int(L/factor)
                yield slice(cur*factor, cur*factor+L), slice(cur, cur+l)
                cur += chunksize
        
        if self.argument.slug == 'wave-group':
            for i in range(self.argument.count):
                for _islice, _oslice in _chunks(inp.shape[1]):
                    yield (i, _oslice, slice(0, None)), (i, _islice)
        else:
            for _islice, _oslice in _chunks(inp.shape[0]):
                yield (_oslice, slice(0, None)), (_islice,)
    
    def scalogram(self, src):
        from scipy.fftpack import fft, ifft, fftshift
        from scipy.signal import resample
        from numpy import complex, exp, abs, arange, newaxis, pi
        
        res = self.result
        scales = (2.5 / res.frequencies * res.time_sampling_rate)[newaxis, :]
        wlen = src.size
        xsd = (arange(-wlen/2., wlen/2.))[:, newaxis] / scales[0, :]
        coefs = exp(complex(1j)*2.*pi*2.5*xsd) * exp(-(xsd**2)/2.) * (scales**-1.)
        del xsd, scales
        
        wf = fft(coefs, axis=0).conj()
        del coefs
        sigf = fft(src)
        wt = abs(fftshift(ifft(sigf[:, newaxis] * wf, axis=0), axes=[0]))
        del wf, sigf
        
        return wt
    
    def handle_job(self, *args, **kwargs):
        from scipy.signal import resample
        
        inp = self.argument.array('r')
        outp = self.result.array('w')
        
        for _o, _i in self.chunks(inp):
            print _o, _i
            _t = _o[1] # timestep slice
            _dt = _t.stop-_t.start # timestep delta
            src = resample(inp[_i], _dt)
            outp[_o] = self.scalogram(src)[None, ...]
        
        inp.close()
        outp.close()
        self.result.done()
    

class ScalogramPowerAnalysis(ProcessingTask):
    name = 'Scalogram power analysis'
    slug = 'scalogram-power-analysis'
    
    argument_types = ('scalogram', 'scalogram-group')
    
    class CriteriaForm(forms.Form):
        freq_start = forms.FloatField(label='First Frequency', required=True, initial=0.25)
        freq_stop = forms.FloatField(label='Last Frequency', required=True, initial=100.0)
    
    def create_component(self, name):
        from neurolab.extensions.basis.waves import Wave, Wavegroup
        cls = Wave if self.argument.slug == 'scalogram' else Wavegroup
        arg = self.argument
        result = self.result = cls(
            parent=arg, 
            block=arg.block,
            name=name,
        )
        for prop in ('dtype', 'count'):
            if hasattr(arg, prop):
                setattr(result, prop, getattr(arg, prop))
        for prop in ('freq_start', 'freq_stop'):
            result.metadata[prop] = self.criteria[prop]
        result.sampling_rate = self.argument.time_sampling_rate
        result.size = result.sampling_rate * arg.length
        result.save()
    
    def handle_job(self, *args, **kwargs):
        from numpy import trapz
        freqz = self.argument.frequencies
        sel = (freqz >= self.criteria['freq_start']) & (freqz <= self.criteria['freq_stop'])
        inp = self.argument.array('r')
        outp = self.result.array('w')
        outp[...] = trapz(inp[..., sel], dx=(1/self.argument.freq_sampling_rate), axis=-1)
        
        inp.close()
        outp.close()
        self.result.done()
    


class ScalogramGrapher(Grapher):
    slug = 'scalogram'
    
    def image_attrs(self):
        cmp = self.component
        return {
            'xmin': 0.0,
            'xmax': cmp.length,
            'ymin': cmp.freq_start,
            'ymax': cmp.freq_stop,
            'vmin': cmp.minimum,
            'vmax': cmp.maximum,
            'type': 'scalogram',
            'oid': str(cmp.id),
        }
    
    def data(self, restricted=True):
        delta_x = self.params['x_stop'] - self.params['x_start']
        delta_y = self.params['y_stop'] - self.params['y_start']
        
        xsampling = self.component.time_sampling_rate
        ysampling = self.component.freq_sampling_rate
        
        xbounds = [int(round(self.params[k] * xsampling)) for k in ('x_start', 'x_stop')]
        ybounds = [int(round(self.params[k] * ysampling)) for k in ('y_start', 'y_stop')]
        
        step = int((delta_x * xsampling) // 1e3) or 1
        xsel = slice(xbounds[0], xbounds[1], step) if restricted else slice(0, None, step)
        ysel = slice(ybounds[0], ybounds[1]) if restricted else slice(0, None)
        
        return self.array[xsel, ysel].transpose()
    
    def process_params(self, params):
        super(ScalogramGrapher, self).process_params(params)
        P = self.params
        
        P['x_start'] = float(params.get('x_start', 0.0))
        P['x_stop'] = float(params.get('x_stop', self.component.length))
        P['y_start'] = float(params.get('y_start', self.component.freq_start))
        P['y_stop'] = float(params.get('y_stop', self.component.freq_stop))
        P['v_min'] = float(params.get('v_min', self.component.minimum))
        P['v_max'] = float(params.get('v_max', self.component.maximum))
        P['colormap'] = params.get('colormap', 'Greys')
    
    def draw_axes(self, ax):
        P = self.params
        ax.imshow(self.data(), interpolation='nearest', aspect='normal', origin='lower',
            vmin=P['v_min'], vmax=P['v_max'], cmap=P['colormap'])
    

class ScalogramGroupGrapher(ScalogramGrapher):
    slug = 'scalogram-group'
    
    def image_attrs(self):
        cmp = self.component
        return {
            'xmin': 0.0,
            'xmax': cmp.length,
            'ymin': cmp.frequencies[0], 
            'ymax': cmp.frequencies[-1],
            'vmins': ",".join(map(str, cmp.minima)),
            'vmaxs': ",".join(map(str, cmp.maxima)),
            'type': 'scalogram-group',
            'oid': str(cmp.id),
            'count': cmp.count,
        }
    
    def data(self, restricted=True):
        from math import floor
        delta_x = self.params['x_stop'] - self.params['x_start']
        delta_y = self.params['y_stop'] - self.params['y_start']
        
        xsampling = self.component.time_sampling_rate
        ysampling = self.component.freq_sampling_rate
        
        xbounds = [int(floor(self.params[k] * xsampling)) for k in ('x_start', 'x_stop')]
        ybounds = [int(floor(self.params[k] * ysampling)) for k in ('y_start', 'y_stop')]
        
        step = int((delta_x * xsampling) // 1e3) or 1
        xsel = slice(xbounds[0], xbounds[1], step) if restricted else slice(0, None, step)
        ysel = slice(ybounds[0], ybounds[1]) if restricted else slice(0, None)
        
        return self.array[self.params['index'], xsel, ysel].transpose()
    
    def process_params(self, params):
        super(ScalogramGroupGrapher, self).process_params(params)
        P = self.params
        
        W = P['index'] = int(params.get('index', 0))
        P['x_start'] = float(params.get('x_start', 0.0))
        P['x_stop'] = float(params.get('x_stop', self.component.length))
        P['y_start'] = float(params.get('y_start', self.component.frequencies[0]))
        P['y_stop'] = float(params.get('y_stop', self.component.frequencies[-1]))
        P['v_min'] = float(params.get('v_min', self.component.minima[W]))
        P['v_max'] = float(params.get('v_max', self.component.maxima[W]))
        P['colormap'] = params.get('colormap', 'Greys')
    


class Scalogram(Component):
    name = 'Scalogram'
    slug = 'scalogram'
    metakeys = metadata('metadata')
    
    time_sampling_rate = FloatField(required=True)
    freq_sampling_rate = FloatField(required=True)
    freq_start = FloatField(required=True)
    freq_stop = FloatField(required=True)
    
    Grapher = ScalogramGrapher
    class CriteriaForm(TimeFrequencyScalogram.CriteriaForm):
        name = forms.CharField(label="Name", required=True)
    
    
    @metakeys.item
    def minimum(self):
        from numpy import min
        with self.array('r') as data:
            return float(min(data))
    
    @metakeys.item
    def maximum(self):
        from numpy import max
        with self.array('r') as data:
            return float(max(data))
    
    
    @property
    def frequencies(self):
        from numpy import linspace
        step = 1/float(self.freq_sampling_rate)
        delta = float(self.freq_stop) - self.freq_start
        return linspace(self.freq_start, self.freq_stop-step, delta/step)
    
    @property
    def dataset_shape(self):
        return (int(self.length*self.time_sampling_rate), len(self.frequencies))
    

class ScalogramGroup(Scalogram):
    name = 'Scalogram Group'
    slug = 'scalogram-group'
    metakeys = metadata('metadata')
    
    count = IntField(required=True, min_value=1)
    
    Grapher = ScalogramGroupGrapher
    class CriteriaForm(Scalogram.CriteriaForm):
        count = forms.IntegerField(label="Wave Count", required=False, min_value=1)
    
    
    @metakeys.item
    def minima(self):
        from numpy import min
        with self.array('r') as data:
            return [
                float(min(data[i]))
                for i in range(self.count)
            ]
    
    @metakeys.item
    def maxima(self):
        from numpy import max
        with self.array('r') as data:
            return [
                float(max(data[i]))
                for i in range(self.count)
            ]
    
    
    @property
    def dataset_shape(self):
        return (self.count, int(self.length*self.time_sampling_rate), len(self.frequencies))
    


Component.registry.extend(Scalogram, ScalogramGroup)
ProcessingTask.tasks.extend(TimeFrequencyScalogram, ScalogramPowerAnalysis)