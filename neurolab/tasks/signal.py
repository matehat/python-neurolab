from neurolab.tasks.base import Task, TaskJob
from neurolab.db.sources import SourceFile, Datasource

class Resample(Task):
    compatible_with = ['hierarchical-data']
    name = 'Resample a signal'
    slug = 'resample-signal'
    
    @classmethod
    def criteria_form(cls, file):
        from django import forms
        return type('CriteriaForm', (forms.Form,), {
            'waves': forms.MultipleChoiceField(label='Waves', help_text='Waves to resample',
                choices=[(ch,ch) for ch in file.metadata['waves']]),
            'sampling_rate': forms.IntegerField(label='Sampling Rate', required=True),
            'output': forms.ChoiceField(required=True, label='Output Location', help_text='Where the extracted section should be saved to',
                choices=[(str(ds.id), ds.name) for ds in Datasource.objects(format__in=formats.writables())])
        })
    
    def create_jobs(self):
        pass
    
    def handle_job(self, job):
        pass
    

class Scalogram(Task):
    compatible_with = ['hierarchical-data']
    name = 'Calculate the time-frequency scalogram'
    slug = 'time-freq-scalogram'


def register_tasks(registry):
    registry.extend(Resample, Scalogram)
