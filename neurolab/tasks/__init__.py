import config
from neurolab.utils import ObjectList
from neurolab.tasks.base import Task

tasks = ObjectList(Task)

for ext in config.TASKS:
    try:
        mod = __import__("neurolab.tasks.%s" % ext, {}, {}, 'register')
        getattr(mod, 'register_tasks', lambda reg: None)(tasks)
    except ImportError:
        continue
