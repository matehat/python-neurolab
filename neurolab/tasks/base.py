from neurolab.db import *
from neurolab.jobs.models import Job
from neurolab.db.sources import SourceFile

class Task(Document):
    file = ReferenceField(SourceFile)
    criteria = DictField()
    
    @classmethod
    def from_criteria(cls, file, form):
        form = cls.criteria_form(file)(form)
        if form.is_valid():
            task = cls(file=file, criteria=form.cleaned_data)
            task.save()
            task.create_jobs()
            return {}
        else:
            return form.errors
    
    
    @property
    def jobs(self, *Q, **kwargs):
        return TaskJob.objects(task=self, *Q, **kwargs)
    
    def create_jobs(self):
        raise NotImplementedError
    
    def handle(self, job):
        raise NotImplementedError
    

class TaskJob(Job):
    task = ReferenceField(Task)
    data = DictField()
    
    def perform(self):
        self.task.handle_job(self)
    

