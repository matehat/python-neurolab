from django import forms

from neurolab.db import *
from neurolab.db.models import *
from neurolab.tasks.models import *
from neurolab.utils import ObjectList

class OutputEntry(Document):
    template = ReferenceField('OutputTemplate')
    block = ReferenceField('Block')
    criteria = DictField()
    
    def make(self, jobdata):
        self.template.make_entry(self, jobdata)
    
    def delete(self, *args, **kwargs):
        self.template.delete_entry(self, *args, **kwargs)
        super(OutputEntry, self).delete()
    

class FileOutputEntry(OutputEntry):
    files = ListField(StringField(), default=lambda: [])


class OutputTemplate(Document):
    dataset = ReferenceField('Dataset')
    name = StringField()
    criteria = DictField()
    
    Entry = OutputEntry
    class CriteriaForm(forms.Form):
        pass
    
    
    def entries(self, *Q, **kwargs):
        return self.Entry.objects(template=self, *Q, **kwargs)
    
    def entry(self, block, criteria):
        entry, created = self.Entry.objects.get_or_create(template=self, block=block)
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
    
    def delete_entry(self, entry):
        pass
    
    def create_jobs(self, entry, task):
        raise NotImplementedError
    


class FileOutputTemplate(OutputTemplate):
    Entry = FileOutputEntry
    
    def create_jobs(self, entry, task):
        for jobdata in self.jobs(entry):
            task.Job(jobdata)
    
    def make_entry(self, entry, jobdata=None):
        block = entry.block
        fname = self.make_filename(entry, jobdata)
        if fname not in entry.files:
            entry.files.append(fname)
            entry.save()
        
        fname = block.dataset.path(block.componentpath(fname), True)
        self.write_file(entry, jobdata, fname)
    
    def delete_entry(self, entry, discard=True):
        block = entry.block
        if discard:
            for fname in entry.files:
                try:
                    block.dataset.unlink(block.componentpath(fname))
                except OSError:
                    continue
    
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
    

class OutputTask(Task):
    job_queue = 'output'
    entry = ReferenceField(OutputEntry)
    
    def handle_job(self, job):
        self.entry.make(job.data)
    


OutputTemplate.templates = ObjectList(OutputTemplate)
