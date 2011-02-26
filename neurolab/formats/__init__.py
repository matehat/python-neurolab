from neurolab.utils import ObjectList
from neurolab.formats.base import BaseFormat
import config

formats = ObjectList(BaseFormat)
def writable_formats():
    return [fmt.slug for fmt in formats if fmt.writable]

formats.writables = writable_formats

for ext in config.SUPPORTED_FORMATS:
    try:
        mod = __import__("neurolab.formats.%s" % ext, {}, {}, 'register')
        getattr(mod, 'register_formats', lambda reg: None)(formats)
    except ImportError:
        continue
