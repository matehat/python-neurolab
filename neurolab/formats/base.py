from neurolab.utils import ObjectList

class FormatMeta(type):
    def __new__(cls, name, bases, attrs):
        abstract = attrs.pop('abstract', False)
        new_class = super(FormatMeta, cls).__new__(cls, name, bases, attrs)
        if hasattr(new_class, 'slug') and not abstract:
            Format.registry.extend(new_class)
        return new_class
    
    def __getitem__(self, name):
        return Format.registry[name]
    

class Format(object):
    __metaclass__ = FormatMeta
    
    def __init__(self, sourcefile):
        self.sourcefile = sourcefile
    
    
    @staticmethod
    def choices():
        return Format.registry.items()
    


Format.registry = ObjectList(Format)