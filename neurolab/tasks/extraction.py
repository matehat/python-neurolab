from neurolab.tasks.base import Task, TaskJob
from neurolab.db.sources import SourceFile, Datasource
from neurolab.formats import formats

class TDExtractSection(Task):
    compatible_with = ['tucker-davis']
    name = 'Extract section of a TD Tank'
    slug = 'tdt-extract-section'
    
    @classmethod
    def criteria_form(cls, file):
        from django import forms
        return type('CriteriaForm', (forms.Form,), {
            'waves': forms.MultipleChoiceField(label='Waves', help_text='Waves to extract from the source file',
                choices=[(ch,ch) for ch in file.metadata['waves']]),
            'groups': forms.MultipleChoiceField(label='Wave Groups', help_text='Wave groups to extract from the source file',
                choices=[(code,code) for code in file.metadata['groups']]),
            
            'starttime': forms.FloatField(required=False, label='Start Time (s)', initial=0.0, 
                min_value=0.0, max_value=file.metadata['length']),
            'endtime': forms.FloatField(required=False, label='End Time (s)', initial=0.0,
                min_value=0.0, max_value=file.metadata['length']),
            
            'output': forms.ChoiceField(required=True, label='Output Location', help_text='Where the extracted section should be saved to',
                choices=[(str(ds.id), ds.name) for ds in Datasource.objects(format__in=formats.writables())])
        })
    
    def create_jobs(self):
        from datetime import datetime
        datasource = Datasource.objects.get(id=self.criteria['output'])
        waves = self.criteria.get('waves', [])
        for group in self.criteria.get('groups', []):
            waves.extend(source_metadata['groups'][group]['waves'])
        
        source_metadata = self.file.metadata
        length = source_metadata['length']
        length -= self.criteria.get('starttime', 0)
        endtime = self.criteria['endtime'] = self.criteria.get('endtime', None) or length
        
        if endtime > length:
            self.criteria['endtime'] = length
        else:
            length -= (length - endtime)
        
        metadata = {
            'waves': {
                ch: {
                    'sampling_rate': source_metadata['waves'][ch]['sampling_rate']
                }
            },
            'recording_time': source_metadata['recording_time'],
            'length': length
        }
        outfile = datasource.newfile(self.file, self.criteria, metadata)
        self.criteria['waves'] = waves
        self.save()
        
        job = TaskJob(task=self, created=datetime.now(), data={'outfile': outfile.id})
        job.set_queue('files')
        job.save()
    
    def handle_job(self, job):
        outfile = SourceFile.objects.get(id=job.data['outfile'])
        outfile.write(self.file.read(self.criteria['waves'], 
            self.criteria.get('starttime', 0), 
            self.criteria.get('endtime', None))
        )
    

class TDExtractSlices(Task):
    compatible_with = ['tucker-davis']
    name = 'Extract slices of a TD Tank'
    slug = 'tdt-extract-slices'
    
    @classmethod
    def criteria_form(cls, file):
        from django import forms
        params = {}
        if file.metadata.get('length') is not None:
            params.update(max_value=file.metadata['length'])
        
        return type('CriteriaForm', (forms.Form,), {
            'waves': forms.MultipleChoiceField(required=False, label='Channels', help_text='Channels to extract from the source file',
                choices=[(ch,ch) for ch in file.metadata['waves']]),
            'groups': forms.MultipleChoiceField(required=False, label='Channel Types', help_text='Channel Types to extract from the source file',
                choices=[(code,code) for code in file.metadata['groups']]),
            
            'starttime': forms.FloatField(required=False, label='Start Time (s)', initial=0.0, 
                min_value=0.0, **params),
            'endtime': forms.FloatField(required=False, label='End Time (s)', initial=0.0,
                min_value=0.0, **params),
            'slice_length': forms.FloatField(required=True, label='Slices Length (s)', initial=0.0,
                min_value=0.0),
            
            'output': forms.ChoiceField(required=True, label='Output Location', help_text='Where the extracted section should be saved to',
                choices=[(str(ds.id), ds.name) for ds in Datasource.objects(format__in=formats.writables())]),
        })
    
    def create_jobs(self):
        from datetime import datetime, timedelta
        datasource = Datasource.objects.get(id=self.criteria['output'])
        cursor = start = self.criteria.get('starttime', 0) or 0
        dtime = self.criteria['slice_length']
        
        end = self.criteria.get('endtime', None)
        if self.criteria.get('endtime', None) is None:
            end = self.file.metadata['length']
        
        source_metadata = self.file.metadata
        waves = self.criteria.get('waves', [])
        for group in self.criteria.get('groups', []):
            waves.extend(source_metadata['groups'][group]['waves'])
        self.criteria['waves'] = waves
        self.save()
        
        base_metadata = {
            'waves': {
                ch: {
                    'sampling_rate': source_metadata['waves'][ch]['sampling_rate']
                }
                for ch in waves
            }
        }
        
        while cursor < end:
            jobdata = self.criteria.copy()
            job = TaskJob(task=self, created=datetime.now(), data={'starttime': cursor})
            cursor = cursor+dtime
            if cursor > end:
                cursor = end
            job.data['endtime'] = cursor
            jobdata.update(job.data)
            
            metadata = base_metadata.copy()
            metadata['length'] = job.data['endtime'] - job.data['starttime']
            metadata['recording_time'] = source_metadata['recording_time'] + timedelta(seconds=job.data['starttime'])
            
            outfile = datasource.newfile(self.file, jobdata, metadata)
            job.data['outfile'] = outfile.id
            job.set_queue('files')
            job.save()
    
    def handle_job(self, job):
        data = self.file.read(self.criteria['waves'], 
            job.data['starttime'], job.data['endtime']
        )
        print data
        SourceFile.objects.get(id=job.data['outfile']).write(
            data
        )
    


def register_tasks(registry):
    registry.extend(TDExtractSection, TDExtractSlices)
