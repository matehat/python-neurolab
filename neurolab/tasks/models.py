from datetime import datetime

import config
from neurolab.db import *
from neurolab.db.models import Component, Block, SourceFile, Dataset
from neurolab.utils import ObjectList

class Job(Document):
    inprogress = BooleanField(default=False)
    queue = ReferenceField('Queue')
    worker = ReferenceField('Worker')
    ready = BooleanField(default=True)
    
    started = DateTimeField()
    created = DateTimeField()
    
    events = ListField(ReferenceField('JobEvent'), default=lambda: [])
    
    def handle_error(self, error, tb=""):
        self.ready = False        
        self.events.append(JobEvent.objects.create(
            occured=datetime.now(),
            message="""%s\nTraceback:\n%s""" % (", ".join(error.args), tb)
        ))
        self.inprogress = False
        self.worker = None
        self.save()
    
    def set_queue(self, queue):
        self.queue = Queue.objects.get(name=queue)
    
    def perform(self):
        raise NotImplementedError
    
    
    def __repr__(self):
        return "Job(id=%s)" % self._id
    

class JobEvent(Document):
    message = StringField()
    occured = DateTimeField()
    meta = {'ordering': ['occured']}


class Signal(Document):
    action = StringField()
    target = GenericReferenceField()

class Worker(Document):
    queue = ReferenceField('Queue')
    pid = IntField()
    
    meta = {'ordering': ['_id']}
    
    def send_signal(self, action):
        Signal.objects.create(target=self, action=action)
    
    
    @property
    def logfile(self):
        return "%s.%s.log" % (self.queue.name, list(Worker.objects(queue=self.queue)).index(self))
    

class Queue(Document):
    name = StringField()
    time = FloatField()
    workers = IntField()
    
    def send_signal(self, action):
        Signal.objects.create(target=self, action=action)
    


class Task(Document):
    criteria = DictField(default=lambda: {})
    
    @property
    def jobs(self, *Q, **kwargs):
        return TaskJob.objects(task=self, *Q, **kwargs)
    
    
    def Job(self, data=None, *args, **kwargs):
        data = {} if data is None else data
        self.save()
        job = TaskJob(task=self, created=datetime.now(),
            data=data,
            *args, **kwargs)
        job.set_queue(self.job_queue)
        job.save()
        return job
    
    def create_jobs(self):
        raise NotImplementedError
    
    def handle_job(self, job):
        raise NotImplementedError
    

class TaskTemplate(Document):
    task = StringField()
    criteria = DictField()
    
    def create_task(self, *args, **kwargs):
        return Task.registry[self.task].objects.create(
            criteria=self.criteria, *args, **kwargs
        )
    

class TaskJob(Job):
    task = ReferenceField(Task)
    data = DictField()
    
    def perform(self):
        self.task.handle_job(self)
    


class LoadTask(Task):
    job_queue = 'files'
    component = ReferenceField(Component)
    
    def create_jobs(self):
        return self.Job()
    
    def handle_job(self, job):
        self.component.load()
        print "Done Loading Component(%s) from File" % self.component.name
    

class ProcessingTask(Task):
    job_queue = 'data'
    argument = ReferenceField(Component)
    result = ReferenceField(Component)
    
    @classmethod
    def create_from_template(cls, template, argument):
        task = cls.create(template.name, argument, template.criteria)
        task.result.template = template
        task.result.save()
        return task
    
    @classmethod
    def create(cls, name, argument, criteria):
        if argument.slug not in cls.argument_types:
            raise TypeError
        
        task = cls(argument=argument, criteria=criteria)
        task.create_component(name)
        task.create_jobs()
        return task
    
    
    def create_component(self, name):
        raise NotImplementedError
    
    def create_jobs(self):
        form = self.CriteriaForm(self.criteria)
        print form.is_valid(), form.errors
        assert self.CriteriaForm(self.criteria).is_valid()
        return [self.Job(jobdict) for jobdict in self.iterjobs()]
    
    
    def iterjobs(self):
        yield {}
    


ProcessingTask.tasks = ObjectList(ProcessingTask)

for queue in ('graphics', 'data', 'files'):
    queue, created = Queue.objects.get_or_create(name=queue)
    if created:
        queue.workers = config.QUEUES[queue.name]['workers']
        queue.time = config.QUEUES[queue.name]['time']
        queue.save()
