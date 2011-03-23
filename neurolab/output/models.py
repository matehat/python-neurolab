from django import forms

from neurolab.db import *
from neurolab.db.models import *
from neurolab.tasks.models import *
from neurolab.utils import ObjectList

class OutputTemplate(Document):
    dataset = ReferenceField(Dataset)
    name = StringField()
    criteria = DictField()
    
    class CriteriaForm(forms.Form):
        pass
    
    
    def entries(self, *Q, **kwargs):
        return OutputEntry.objects(template=self, *Q, **kwargs)
    
    def entry(self, block, criteria):
        entry, created = OutputEntry.objects.get_or_create(template=self, block=block)
        if created:
            crit = {}
            crit.update(self.criteria)
            crit.update(criteria)
            crit = self.CriteriaForm(crit)
            if crit.is_valid():
                crit = crit.cleaned_data
            else:
                raise TypeError("The provided criteria are not valid.")
            
            entry.criteria = crit
            entry.save()
            
            task = OutputTask.objects.create(entry=entry)
            self.create_jobs(entry, task)
        return entry
    
    def make_entry(self, entry, jobdata=None):
        raise NotImplementedError
    
    def create_jobs(self, entry, task):
        raise NotImplementedError
    

class FileOutputTemplate(OutputTemplate):
    def create_jobs(self, entry, task):
        for jobdata in self.jobs(entry):
            task.Job(jobdata)
    
    def make_entry(self, entry, jobdata=None):
        block = entry.block
        fname = block.dataset.path(
            block.componentpath(self.make_filename(entry, jobdata)),
            True
        )
        self.write_file(entry, jobdata, fname)
    
    def delete_entry(self, entry):
        block.dataset.unlink(
            block.componentpath(self.make_filename(entry, jobdata))
        )
    
    def jobs(self, entry):
        raise NotImplementedError
    
    def make_filename(self, entry, jobdata=None):
        raise NotImplementedError
    
    def write_file(entry, jobdata, fname):
        raise NotImplementedError
    

class ImageOutputTemplate(FileOutputTemplate):
    def write_file(entry, jobdata, _file):
        from matplotlib import pyplot
        figure = pyplot.figure()
        self.draw_figure(entry, jobdata, figure)
        self.save_figure(entry, jobdata, figure, _file)
        pyplot.close(figure)
    
    def draw_figure(entry, jobdata, fig):
        raise NotImplementedError
    
    def save_figure(entry, jobdata, fig, _file):
        fig.savefig(_file)
    

class OutputEntry(Document):
    template = ReferenceField(OutputTemplate)
    block = ReferenceField(Block)
    criteria = DictField()
    
    def make(self, jobdata):
        self.template.make_entry(self, jobdata)
    

class OutputTask(Task):
    job_queue = 'output'
    entry = ReferenceField(OutputEntry)
    
    def handle_job(self, job):
        self.entry.make(job.data)
    

OutputTemplate.templates = ObjectList(OutputTemplate)