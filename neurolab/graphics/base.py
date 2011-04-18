from matplotlib import pyplot as plt
import numpy as np

mimetypes = {
    'png': 'image/png',
    'pdf': 'application/pdf',
    'eps': 'application/postscript',
    'ps': 'application/postscript',
    'svg': 'image/svg+xml'
}

class Grapher(object):
    def __init__(self, component, params=None):
        if component.slug != self.slug:
            raise Grapher.ComponentNotCompatible
        self.component = component
        self.array = component.array('r')
        self.params = params or {}
    
    
    class ComponentNotCompatible(TypeError):
        pass
    
    class FormatNotSupported(TypeError):
        pass
    
    class ParameterRequired(KeyError):
        pass
    
    
    @property
    def params(self):
        return self._params
    
    @params.setter
    def params(self, params):
        self.process_params(params)
    
    
    def process_params(self, params):
        self._params = {}
    
    
    def image_htmlattrs(self):
        from django.forms.util import flatatt
        from django.utils.safestring import mark_safe
        return mark_safe(flatatt(
            {"data-%s" % k: v for k, v in self.image_attrs().iteritems()}
        ))
    
    
    def create_axes(self):
        self.axes = [plt.Axes(self._figure, [0., 0., 1., 1.])]
        [ax.set_axis_off() for ax in self.axes]
        self._figure.add_axes(*self.axes)
    
    def draw_axes(self):
        raise NotImplementedError
    
    def get_image(self, width, height, format):
        if format not in mimetypes:
            raise Grapher.FormatNotSupported
        from cStringIO import StringIO
        self.width = float(width)
        self.height = float(height)
        
        w,h = [l/72 for l in (self.width, self.height)]
        self.figure.set_size_inches(w,h)
        self.create_axes()
        self.draw_axes()
        data = StringIO()
        self.figure.savefig(data, dpi=72, format=format)
        self.close_figure()
        return data, mimetypes[format]
    
    
    @property
    def figure(self):
        if not hasattr(self, '_figure'):
            self._figure = plt.figure(frameon=False)
        return self._figure
    
    def close_figure(self):
        plt.close(self.figure)
        delattr(self, '_figure')
        self.array.close()
    


class WaveGrapher(Grapher):
    slug = 'wave'
    
    def image_attrs(self):
        cmp = self.component
        return {
            'xmin': 0.0, 'xmax': cmp.length,
            'ymin': cmp.minimum, 'ymax': cmp.maximum,
            'type': 'wave',
            'oid': str(cmp.id),
        }
    
    
    def Y(self, restricted=True):
        from math import floor
        delta_x = self.params['x_stop'] - self.params['x_start']
        sampl = self.component.sampling_rate
        bounds = [int(round(self.params["x_%s" % k] * sampl)) for k in ('start', 'stop')]
        
        if hasattr(self, 'width'):
            N = delta_x * sampl
            factor = floor(N / self.width)
        else:
            factor = 1
        sel = slice(bounds[0], bounds[1], 1) if restricted else slice(0, None, factor)
        return self.array[sel]
    
    def T(self):
        return np.linspace(self.params['x_start'], self.params['x_stop'], self.Y().size)
    
    def process_params(self, params):
        super(WaveGrapher, self).process_params(params)
        P = self.params
        P['x_start'] = float(params.get('x_start', 0.0))
        P['x_stop'] = float(params.get('x_stop', self.component.length))
        
        y = self.Y(False)
        P['y_start'] = float(params.get('y_start', self.component.minimum))
        P['y_stop'] = float(params.get('y_stop', self.component.maximum))
        P['linewidth'] = float(params.get('linewidth', 1.0))
        P['linecolor'] = params.get('linecolor', '#333333')
    
    def draw_axes(self):
        ax, = self.axes
        ax.set_ylim(*[self.params["y_%s" % k] for k in ('start', 'stop')])
        ax.set_xlim(*[self.params["x_%s" % k] for k in ('start', 'stop')])
        ax.plot(self.T(), self.Y(), lw=self.params['linewidth'], c=self.params['linecolor'])
    

class WaveGroupGrapher(WaveGrapher):
    slug = 'wave-group'
    
    def image_attrs(self):
        cmp = self.component
        return {
            'xmin': 0.0, 'xmax': cmp.length,
            'ymins': ",".join(map(str, cmp.minima)), 
            'ymaxs': ",".join(map(str, cmp.maxima)),
            'count': cmp.count,
            'type': 'wave-group',
            'oid': str(cmp.id),
        }
    
    def Y(self, restricted=True):
        delta_x = self.params['x_stop'] - self.params['x_start']
        sampl = self.component.sampling_rate
        bounds = [int(round(self.params["x_%s" % k] * sampl)) for k in ('start', 'stop')]
        
        arr = self.array
        step = int((delta_x * sampl) // 1e6) or 1
        sel = slice(bounds[0], min(bounds[1], arr.shape[1]), step) if restricted else slice(0, None, step)
        return arr[self.params['index'], sel]
    
    def process_params(self, params):
        super(WaveGrapher, self).process_params(params)
        P = self.params
        W = P['index'] = int(params.get('index', 0))
        P['x_start'] = float(params.get('x_start', 0.0))
        P['x_stop'] = float(params.get('x_stop', self.component.length))
        
        y = self.Y(False)
        P['y_start'] = float(params.get('y_start', self.component.minima[W]))
        P['y_stop'] = float(params.get('y_stop', self.component.maxima[W]))
        P['linewidth'] = float(params.get('linewidth', 1.0))
        P['linecolor'] = params.get('linecolor', '#333333')
    


__all__ = ('WaveGroupGrapher', 'WaveGrapher')