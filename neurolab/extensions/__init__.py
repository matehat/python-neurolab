import config

for ext in config.TASKS:
    mod = __import__("neurolab.extensions.%s" % ext, {}, {}, 'ProcessingTask')
