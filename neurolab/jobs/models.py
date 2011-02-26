from neurolab.db import *
import config

class Job(Document):
    inprogress = BooleanField(default=False)
    queue = ReferenceField('Queue')
    worker = ReferenceField('Worker')
    ready = BooleanField(default=True)
    
    started = DateTimeField()
    created = DateTimeField()
    
    events = ListField(ReferenceField('JobEvent'))
    
    def set_queue(self, queue):
        self.queue = Queue.objects.get(name=queue)
    
    def perform(self):
        raise NotImplementedError
    
    def __repr__(self):
        return "Job(id=%s)" % self._id
    

class JobEvent(Document):
    message = StringField()
    occured = DateTimeField()
    meta = {
        'ordering': ['occured']
    }


class Signal(Document):
    action = StringField()
    target = GenericReferenceField()

class Worker(Document):
    queue = ReferenceField('Queue')
    pid = IntField()

class Queue(Document):
    name = StringField()
    time = FloatField()
    workers = IntField()


for queue in ('graphics', 'data', 'files'):
    queue, created = Queue.objects.get_or_create(name=queue)
    if created:
        queue.workers = config.QUEUES[queue.name]['workers']
        queue.time = config.QUEUES[queue.name]['time']
        queue.save()
    
