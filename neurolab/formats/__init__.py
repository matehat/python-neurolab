from neurolab.formats.base import Format
import config

for ext in config.FILEFORMATS:
    try:
        mod = __import__("neurolab.formats.%s" % ext, {}, {}, 'register')
    except ImportError:
        continue
