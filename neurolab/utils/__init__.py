from UserDict import DictMixin

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

def options(defaults):
    def decorate(function):
        def caller(*args, **kwargs):
            opts = defaults.copy()
            args = list(args)
            opts.update(kwargs)
            if isinstance(args[-1], dict):
                opts.update(args.pop())
            args.append(opts)
            return function(*args)
        
        caller.__doc__ = function.__doc__
        caller.__name__ = function.__name__
        return caller
    
    return decorate

def dictitems(_dict):
    if isinstance(_dict, dict):
        return tuple([(k, dictitems(_dict[k])) for k in sorted(_dict.keys())])
    else:
        return _dict


class metadata(object):
    def __init__(self, property):
        self.items = {}
        self.instance = None
        self.property = property
    
    def __get__(self, instance, owner):
        if instance is not None:
            self.instance = instance
        return self
    
    def __iter__(self):
        return self.items.iterkeys()
    
    def __repr__(self):
        return repr(self.items.keys())
    
    
    @property
    def dict(self):
        return getattr(self.instance, self.property)
    
    def item(self, func):
        key = func.__name__
        self.items[key] = func
        
        def pfunc(_self):
            self.instance = _self
            if self.dict.get(key, None) is None:
                self.cache(key, save=True)
            return self.dict[key]
        
        pfunc.__name__ = key
        pfunc.__doc__ = func.__doc__
        return property(pfunc)
    
    def cache(self, key=None, save=False):
        if key is None:
            map(self.cache, self.items)
        else:
            self.dict[key] = self.items[key](self.instance)
        if save:
            self.instance.save()
    


class ObjectList(object):
    def __init__(self, base_class, *objects):
        self.base_class = base_class
        self.objects = []
        self.extend(*objects)
    
    def __getitem__(self, key):
        for obj in self:
            if obj.slug == key:
                return obj
        raise KeyError
    
    def __iter__(self):
        return iter(self.objects)
    
    
    def items(self):
        return self.objects[:]
    
    def extend(self, *objects):
        if any([not issubclass(obj, self.base_class) for obj in objects]):
            raise TypeError
        self.objects.extend(objects)
    
    
    @property
    def slugs(self):
        if not hasattr(self, '_slugs'):
            self._slugs = [obj.slug for obj in self]
        return self._slugs
    

class DictWrapperProxy(DictMixin):
    def __init__(self, keys, values):
        self._keys = tuple(keys)
        self._values = tuple(values)
    
    def __getitem__(self, k):
        if k in self._keys:
            return self._values[self._keys.index(k)]
        raise KeyError
    
    def __setitem__(self, k, v):
        if k not in self._keys:
            self._keys.append(k)
            self._values.append(v)
        else:
            self._values[self._keys.index(k)] = v
    
    def keys(self):
        return self._keys
    
    def __iter__(self):
        return iter(self._keys)
    
    def iteritems(self):
        for i in range(len(self._keys)):
            yield self._keys[i], self._values[i]
    
    def __contains__(self, k):
        return k in self._keys
    
    def copy(self):
        return dict(*list(self.iteritems()))
    

class DictWrapper(object):
    def __init__(self, keys_prop, values_prop, cached_name=None):
        self.keys_prop = keys_prop
        self.values_prop = values_prop
        self.cached_name = cached_name
    
    def __get__(self, instance, owner):
        if self.cached_name is None or \
                getattr(instance, self.cached_name, None) is None:
            proxy = DictWrapperProxy(getattr(instance, self.keys_prop), 
                getattr(instance, self.values_prop))
            if self.cached_name is not None:
                setattr(instance, self.cached_name, proxy)
            return proxy
        else:
            return getattr(instance, self.cached_name)
    
    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError
        keys, values = [], []
        for k,v in value.iteritems():
            keys.append(k)
            values.append(v)
        
        setattr(instance, self.keys_prop, keys)
        setattr(instance, self.values_prop, values)
    

class FormattedString(object):
    def __init__(self, string):
        self.string = string
    
    def __get__(self, instance, owner):
        return self.string.format(self=instance, cls=owner)
    
