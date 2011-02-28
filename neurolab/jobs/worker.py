import time
import os
import sys
import atexit

from pymongo.dbref import DBRef

import config
from neurolab.jobs.models import *
from neurolab.tasks import *
from neurolab.db import mongodb

os.environ['DJANGO_SETTINGS_MODULE'] = 'httpserver.settings'

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit(0)
    else:
        worker = Worker.objects.get(pk=sys.argv[1])
    
    def cleanup():
        worker.pid = None
        worker.save()
    
    atexit.register(cleanup)
    
    collection = Job._meta['collection']
    wref = DBRef(Worker._meta['collection'], worker.id)
    
    queue = worker.queue
    qref = DBRef(Queue._meta['collection'], queue.id)
    
    print "Watching job queue (%s.%s) for jobs to consume" % (config.MONGO_DB, collection)
    print "Worker ID : %s" % worker.id
    
    while True:
        coll = mongodb(collection)
        obj = coll.find_and_modify(
            {'inprogress': False, 'ready': True, 'queue': qref},
            {'$set': {'worker': wref, 'inprogress': True}},
            sort={'order': 1},
            upsert=False
        )
        if obj is not None:
            job = Job._from_son(obj)
            print "Got a job: %s" % repr(job)
            
            try:
                job.perform()
                coll.remove({'_id': obj['_id']})
            except Exception as e:
                print e
                raise
                job.handle_error(e)
                job.inprogress = False
                job.worker = None
                job.save()
            del obj, job
            continue
        
        time.sleep(queue.time)
