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
    
    def __repr__(self):
        return 'Datasource(format=%s, root=%s)' % (self.format, self.root)
    
    
    def _match(self, _regexp, path):
        reg = _regexp
        if not reg.startswith('^'):
            reg = "^%s" % reg
        match = re.match(reg, path)
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
            regexp = self.levels[lindex]
            data = self._match(regexp, name)
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
                        pathdata=_data, 
                        path=join(path, name),
                        datasource=self
                    )
                    files.append(srcfile)
        return files
    
    
    def newfile(self, input, task):
        formatdict = {}
        formatdict.update(input.metadata)
        formatdict.update(task)
        path = self.nameformat.format(**formatdict)
        
        srcfile = SourceFile(datasource=self, path=path, _metadata=formatdict)
        srcfile.save()
        return srcfile
    
    
    @property
    def fileformat(self):
        return formats[self.format]
    
    @property
    def files(self, *Q, **kwargs):
        self._parse()
        return SourceFile.objects(datasource=self, *Q, **kwargs)
    


class SourceFile(Document):
    pathdata = DictField()
    _metadata = DictField()
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
        if not self._metadata:
            self._metadata = self.pathdata
            self._metadata.update(self.fileformat.filedata())
        return self._metadata
    
    def read(self, components, starttime=0, endtime=None):
        return self.fileformat.read_dataset(components, starttime, endtime)
    
    def write(self, components):
        return self.fileformat.write_dataset(components)
    

class Task(Document):
    file = ReferenceField(SourceFile)
    criteria = DictField()
    
    @classmethod
    def from_criteria(cls, file, form):
        form = cls.criteria_form(file)(form)
        if form.is_valid():
            task = cls(file=file, criteria=form.cleaned_data)
            task.save()
            task.create_jobs()
            return {}
        else:
            return form.errors
    
    
    @property
    def jobs(self, *Q, **kwargs):
        return Job.objects(task=self, *Q, **kwargs)
    
    def create_jobs(self):
        raise NotImplementedError
    
    def handle(self, job):
        raise NotImplementedError
    

class TaskJob(_Job):
    task = ReferenceField(Task)
    data = DictField()
    
    def perform(self):
        self.task.handle_job(self)
    


class TaskGroup(object):
    def __init__(self, name):
        self.name = name
        self.tasks = []
        TaskGroup
    
    
    def extend(self, *tasks):
        self.tasks.extend(tasks)
    
    def get_for_format(self, format):
        return [
            task for task in self.tasks
            if task.compatible_with == 'all' or format in task.compatible_with
        ]
    


class ExtractSection(Task):
    compatible_with = ['tucker-davis']
    name = 'Extract section of a file'
    
    @classmethod
    def criteria_form(cls, file):
        from django import forms
        return type('CriteriaForm', (forms.Form,), {
            'channels': forms.MultipleChoiceField(required=True, label='Channels', help_text='Channels to extract from the source file',
                choices=[(ch,ch) for ch in file.metadata['channels']]),
            'starttime': forms.FloatField(required=False, label='Start Time (s)', initial=0.0, 
                min_value=0.0, max_value=file.metadata['length']),
            'endtime': forms.FloatField(required=False, label='End Time (s)', initial=0.0,
                min_value=0.0, max_value=file.metadata['length']),
            'output': forms.ChoiceField(required=True, label='Output Location', help_text='Where the extracted section should be saved to',
                choices=[(str(ds.id), ds.name) for ds in Datasource.objects(format__in=formats.writables())])
        })
    
    def create_jobs(self):
        from datetime import datetime
        datasource = Datasource.objects.get(id=self.criteria['output'])
        outfile = datasource.newfile(self.file, self.criteria)
        
        job = TaskJob(task=self, created=datetime.now(), data={'outfile': outfile.id})
        job.set_queue('files')
        job.save()
    
    def handle_job(self, job):
        outfile = SourceFile.objects.get(id=job.data['outfile'])
        outfile.write(self.file.read(self.criteria['channels'], self.criteria['starttime'] or 0, 
            self.criteria['endtime'] or None))
    

class ExtractSlices(Task):
    compatible_with = ['tucker-davis']
    name = 'Extract slices of a file'
    
    @classmethod
    def criteria_form(cls, file):
        from django import forms
        params = {}
        if file.metadata.get('length') is not None:
            params.update(max_value=file.metadata['length'])
        
        return type('CriteriaForm', (forms.Form,), {
            'channels': forms.MultipleChoiceField(required=True, label='Channels', help_text='Channels to extract from the source file',
                choices=[(ch,ch) for ch in file.metadata['channels']]),
            'starttime': forms.FloatField(required=False, label='Start Time (s)', initial=0.0, 
                min_value=0.0, **params),
            'endtime': forms.FloatField(required=False, label='End Time (s)', initial=0.0,
                min_value=0.0, **params),
            'output': forms.ChoiceField(required=True, label='Output Location', help_text='Where the extracted section should be saved to',
                choices=[(str(ds.id), ds.name) for ds in Datasource.objects(format__in=formats.writables())]),
            'slice_length': forms.FloatField(required=True, label='Slices Length (s)', initial=0.0,
                min_value=0.0),
        })
    
    def create_jobs(self):
        from datetime import datetime
        datasource = Datasource.objects.get(id=self.criteria['output'])
        cursor = start = self.criteria.get('starttime', 0)
        dtime = self.criteria['slice_length']
        
        end = self.criteria.get('endtime', None)
        if self.criteria.get('endtime', None) is None:
            end = self.file.metadata['length']
        
        print cursor, end, start, dtime
        while cursor < end:
            jobdata = self.criteria.copy()
            job = TaskJob(task=self, created=datetime.now(), data={'starttime': cursor})
            cursor = cursor+dtime
            if cursor > end:
                cursor = end
            job.data['endtime'] = cursor
            jobdata.update(job.data)
            
            job.data['outfile'] = datasource.newfile(self.file, jobdata).id
            job.set_queue('files')
            job.save()
    
    def handle_job(self, job):
        outfile = SourceFile.objects.get(id=job.data['outfile'])
        outfile.write(self.file.read(self.criteria['channels'], job.data['starttime'], job.data['endtime']))
    


FileExtraction = TaskGroup('File Conversion')
FileExtraction.extend(ExtractSection, ExtractSlices)
