from django import forms

import config
from neurolab.tasks.models import ProcessingTask
from neurolab.extensions.basis.waves import WaveProcessingTask

class FFT(WaveProcessingTask):
    name = 'Fast-Fourier Transform'
    slug = 'fft'
    
    class CriteriaForm(forms.Form):
        n = forms.IntegerField(label='Length of Fourier Transform', required=False)
    


ProcessingTask.tasks.extend(FFT)