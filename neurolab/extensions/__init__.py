import config

for ext in config.EXTENSIONS:
    try:
        mod = __import__("neurolab.extensions.%s" % ext, {}, {}, 'ProcessingTask')
        mod = __import__("neurolab.extensions.%s" % ext, {}, {}, 'OutputTemplate')
    except ImportError:
        pass
