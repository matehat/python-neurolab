import string, re, os.path

from neurolab.db import *
from neurolab.jobs.models import Job as _Job
from neurolab.formats import formats

class Location(SafeDocument):
    '''
    Location is a base class that define a set of 
    methods for usual filesystem access. It implements
    basic file operation, like 'open', 'join', 'move',
    etc. It has several fields : 
    
        - root: Root directory in the filesystem
        - name: User-defined name
    '''
    root = StringField(required=True)
    name = StringField()
    
    @property
    def available(self):
        from os.path import exists
        return exists(self.root)
    
    
    def tempfile(self, mode='w+b', prefix='', dir=''):
        from tempfile import NamedTemporaryFile
        return NamedTemporaryFile(mode=mode, prefix=prefix, dir=self.join(dir), delete=False)
    
    def mtime(path):
        import stat, datetime, os
        return datetime.datetime.fromtimestamp(
            os.stat(self.path(path))[stat.ST_MTIME]
        )
    
    def move(self, src, dst):
        from shutil import move
        move(self.path(src), self.path(dst))
    
    def rmtree(self, path):
        from shutil import rmtree
        rmtree(self.path(path))
    
    def open(self, path, *args):
        return open(self.path(path), *args)
    
    def path(self, *paths):
        from os.path import join
        path = join(*paths)
        if not path.startswith(self.root):
            path = join(self.root, path)
        return path
    
    join = path
    def remove(self, path):
        from os import remove
        remove(self.path(path))
    
    unlink = remove
    def exists(self, path):
        from os.path import exists
        return exists(self.path(path))
    
    def mkdirs(self, path):
        from os.path import split
        base, name = split(path)
        self.mkdir(base)
    
    def mkdir(self, path):
        from os import makedirs
        path = self.path(path)
        if not self.exists(path):
            makedirs(path)
    

class Datasource(Location):
    '''
    A Datasource is a user-defined Location that
    can parse itself to provide a set of SourceFiles.
    '''
    levels = ListField(StringField())
    nameformat = StringField()
    format = StringField()
    
    def __init__(self, *args, **kwargs):
        super(Datasource, self).__init__(*args, **kwargs)
        def compile_level(lvl):
            if not lvl.startswith('^'):
                lvl = "^%s" % lvl
            return re.compile(lvl)
        
        self.relevels = [compile_level(lvl) for lvl in self.levels]
    
    def __repr__(self):
        return 'Datasource(format=%s, root=%s)' % (self.format, self.root)
    
    
    def _match(self, lindex, path):
        match = self.relevels[lindex].match(path)
        if match is not None:
            return match.groupdict()
        else:
            return None
    
    def _parse(self, path='', lindex=0, base=None):
        from os.path import join, isdir
        from os import listdir
        
        files = []
        newpath = join(self.root, path)
        if not isdir(newpath):
            return files
        
        for name in listdir(newpath):
            data = self._match(lindex, name)
            if data is not None:
                _data = (base or {}).copy()
                _data.update(data)
                if len(self.levels) > (lindex+1):
                    files.extend(self._parse(
                        join(path, name),
                        lindex+1, _data
                    ))
                else:
                    srcfile, created = SourceFile.objects.get_or_create(
                        file_data=_data,
                        parsed=False,
                        path=join(path, name),
                        datasource=self
                    )
                    if created:
                        srcfile.meta_data = _data
                        srcfile.save()
                    files.append(srcfile)
        return files
    
    
    def parsetree(self):
        self._parse()
    
    def newfile(self, input, task, metadata):
        formatdict = {}
        formatdict.update(input.metadata)
        formatdict.update(task)
        path = self.nameformat.format(**formatdict)
        
        srcfile = SourceFile(datasource=self, path=path, meta_data=metadata)
        srcfile.save()
        return srcfile
    
    
    @property
    def fileformat(self):
        return formats[self.format]
    
    def files(self, *Q, **kwargs):
        if kwargs:
            for k in kwargs:
                if not k.startswith('meta_data__'):
                    val = kwargs.pop(k)
                    kwargs['meta_data__%s' % k] = val
        
        return SourceFile.objects(datasource=self, *Q, **kwargs)
    

class SourceFile(Document):
    meta_data = DictField()
    file_data = DictField()
    parsed = BooleanField(default=True)
    path = StringField()
    datasource = ReferenceField(Datasource)
    
    def __repr__(self):
        return u"SourceFile(path=%s)" % self.path
    
    
    @property
    def fileformat(self):
        if not hasattr(self, '_fileformat'):
            self._fileformat = self.datasource.fileformat(self)
        return self._fileformat
    
    @property
    def ready(self):
        return self.exists()
    
    @property
    def fullpath(self):
        return self.datasource.path(self.path)
    
    
    def mkdirs(self):
        self.datasource.mkdirs(self.path)
    
    def exists(self):
        return self.datasource.exists(self.path)
    
    
    @property
    def metadata(self):
        if not self.parsed:
            self.meta_data.update(self.fileformat.metadata())
            self.parsed = True
#            self.save()
        return self.meta_data
    
    def read(self, components, starttime=0, endtime=None):
        return self.fileformat.read_dataset(components, starttime, endtime)
    
    def write(self, components):
        return self.fileformat.write_dataset(components)
    

