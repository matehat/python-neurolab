import re
from django import forms

from neurolab.utils import ObjectList
from neurolab.formats import Format
from neurolab.db import *
from neurolab.graphics import *

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
        paths = list(paths)
        create = paths[-1] in (True, False) and paths.pop(-1)
        path = join(*paths)
        if create:
            self.mkdirs(path)
        
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
    pathlevels = ListField(StringField())
    treelevels = ListField(StringField())
    fileformat = StringField()
    
    def __repr__(self):
        return 'Datasource(format=%s, root=%s)' % (self.fileformat, self.root)
    
    
    def _match_path(self, lindex, path):
        match = self.compiled_levels[lindex].match(path)
        if match is not None:
            return match.groupdict()
        else:
            return None
    
    def _parse_tree(self, path='', lindex=0, base=None):
        from os.path import join, isdir
        from os import listdir
        
        newpath = join(self.root, path)
        if not isdir(newpath):
            return
        
        files = {}
        for name in listdir(newpath):
            data = self._match_path(lindex, name)
            if data is not None:
                file_data = (base or {}).copy()
                file_data.update(data)
                if len(self.pathlevels) > (lindex+1):
                    prec = self._parse_tree(join(path, name), lindex+1, file_data)
                    if prec is not None:
                        files.update(prec)
                else:
                    files[join(path, name)] = file_data
        
        if base is None:
            currents = set(self.files().distinct('path'))
            newfiles = set(files.keys()) - currents
            docs = [SourceFile(path=path, file_data=files[path], datasource=self).to_mongo()
                for path in newfiles]
            if len(docs) > 0:
                SourceFile.objects._collection.insert(docs, safe=True)
        else:
            return files
    
    
    @property
    def compiled_levels(self):
        def compile_level(lvl):
            if not lvl.startswith('^'):
                lvl = "^%s" % lvl
            return re.compile(lvl)
        
        if not hasattr(self, '_compiled_levels'):
            self._compiled_levels = [compile_level(lvl) for lvl in self.pathlevels]
        return self._compiled_levels
    
    
    def parsetree(self):
        self._parse_tree()
    
    
    def files(self, *Q, **kwargs):
        if kwargs:
            for k in kwargs:
                if not k.startswith('file_data__'):
                    val = kwargs.pop(k)
                    kwargs['file_data__%s' % k] = val
        
        return SourceFile.objects(datasource=self, *Q, **kwargs)
    
    def filetree(self):
        from neurolab.utils import dictitems
        tree = {}
        for file in self.files():
            sub = tree
            for i,level in enumerate(self.treelevels):
                val = level.format(**file.file_data)
                if i == len(self.treelevels) - 1:
                    sub[val] = file
                    continue
                if val not in sub:
                    sub[val] = {}
                sub = sub[val]
        return tree
    

class SourceFile(Document):
    file_data = DictField()
    _infos = DictField()
    path = StringField()
    datasource = ReferenceField(Datasource)
    
    def __repr__(self):
        return u"SourceFile(path=%s)" % self.path
    
    
    @property
    def available(self):
        return self.datasource.exists(self.fullpath)
    
    @property
    def fileformat(self):
        if not hasattr(self, '_fileformat'):
            self._fileformat = Format[self.datasource.fileformat](self)
        return self._fileformat
    
    @property
    def fullpath(self):
        return self.datasource.path(self.path)
    
    @property
    def infos(self):
        if not self._infos:
            self._infos = self.fileformat.get_infos()
            self.save()
        return self._infos
    
    @property
    def components(self):
        return self.infos.get('components', {})
    
    
    def datasets(self):
        datasets = Dataset.objects(id__nin=[
            ref.id for ref in Block.objects(sourcefile=self).distinct('dataset')
        ])
        
        if not 'components' in self.infos:
            return []
        
        file_components = self.components
        def test_dataset(dataset):
            for component in dataset.components:
                print component.name, file_components
                if component.name not in file_components:
                    return False
                file_component = file_components[component.name]
                criteria = Component.registry[file_component['type']].CriteriaForm(file_component)
                if not criteria.is_valid():
                    return False
                #criteria = criteria.cleaned_data
                #for k in criteria:
                #    if criteria[k] != component.criteria[k]:
                #        return False
            return True
        
        return filter(test_dataset, datasets)
    
    def mkdirs(self):
        self.datasource.mkdirs(self.path)
    
    def read_into(self, component, array):
        self.fileformat.read_into(component, array)
    


class Dataset(Location):
    components = ListField(ReferenceField('ComponentTemplate'))
    blockname = StringField(required=True)
    groupname = StringField()
    
    def __repr__(self):
        return u"Dataset(%s, root=%s)" % (self.name, self.root)
    
    
    class IncompatibleFile(Exception):
        pass
    
    
    def load_file(self, file):
        block = Block.objects.create(dataset=self, sourcefile=file)
        block.load()
        return block
    
    
    def blocks(self, *Q, **kwargs):
        return Block.objects(dataset=self, *Q, **kwargs)
    
    def groups(self):
        groups = {}
        for block in self.blocks():
            groups.setdefault(block.group, []).append(block)
        return ((grp, sorted(groups[grp], lambda x,y: cmp(x.name, y.name))) 
            for grp in sorted(groups.keys()))
    

class Block(Document):
    length = FloatField()
    starttime = DateTimeField()
    metadata = DictField()
    
    sourcefile = ReferenceField(SourceFile)
    dataset = ReferenceField(Dataset)
    
    def __repr__(self):
        return u"Block(%s, %s)" % (self.group, self.name)
    
    
    @property
    def templates(self):
        return self.dataset.components
    
    @property
    def name(self):
        starttime = self.starttime
        try:
            name = self.dataset.blockname.format(
                day=starttime.day, month=starttime.month,
                year=starttime.year, **self.metadata
            )
            return name
        except KeyError:
            return self.dataset.blockname
    
    @property
    def group(self):
        starttime = self.starttime
        return self.dataset.groupname.format(
            day=starttime.day, month=starttime.month,
            year=starttime.year, **self.metadata
        )
    
    @property
    def fullpath(self):
        return self.dataset.path(self.group, self.name)
    
    
    def load(self):
        infos = self.sourcefile.infos
        self.starttime = infos['starttime']
        self.length = infos['length']
        self.metadata = self.sourcefile.file_data
        self.save()
        
        try:
            map(lambda t: t.create_from_source(self), self.templates)
        except:
            for component in self.components():
                component.delete()
            raise
    
    def components(self, *Q, **kwargs):
        return Component.objects(block=self, *Q, **kwargs).order_by('+name')
    
    def componentpath(self, component_name):
        from os.path import join
        return join(self.group, self.name, component_name)
    


class ComponentTemplate(Document):
    component_slug = StringField()
    task_slug = StringField()
    
    criteria = DictField()
    name = StringField()
    
    discard = BooleanField(default=False)
    parent = ReferenceField('ComponentTemplate')
    
    def __repr__(self):
        return "ComponentTemplate(%s, %s)" % (self.name,
            "task=%s" % self.task.name if self.task_slug else
            "source=%s" % self.component.name
        )
    
    @property
    def component(self):
        if not hasattr(self, '_component'):
            self._component = Component.registry[self.component_slug]
        return self._component
    
    @property
    def task(self):
        from neurolab.tasks import ProcessingTask
        if not hasattr(self, '_task'):
            self._task = ProcessingTask.tasks[self.task_slug]
        return self._task
    
    @property
    def fields(self):
        if self.component_slug:
            return self.component._fields
        else:
            return self.task._fields
    
    
    def offspring(self, *Q, **kwargs):
        return ComponentTemplate.objects(parent=self, *Q, **kwargs)
    
    def instances(self, *Q, **kwargs):
        return Component.objects(template=self, *Q, **kwargs)
    
    
    def update(self):
        map(lambda c: c.update(), self.instances(ready=True))
    
    
    def create_from_source(self, block):
        from neurolab.tasks import LoadTask
        component = self.component(block=block, ready=False, template=self)
        criteria = block.sourcefile.components[self.name]
        
        for key in criteria:
            if key not in self.fields:
                continue
            #if key in self.criteria:
                #if self.criteria[key] != criteria[key]:
                #    raise Dataset.IncompatibleFile
            setattr(component, key, criteria[key])
        component.save()
        
        task = LoadTask.objects.create(component=component)
        task.create_jobs()
        
        return component
    
    def create_for_task(self, parent):
        return self.task.create_from_template(template=self, argument=parent).result
    

class Component(Document):
    block = ReferenceField(Block)
    ready = BooleanField(default=False)
    discarded = BooleanField(default=False)
    
    template = ReferenceField('ComponentTemplate')
    parent = ReferenceField('Component')
    
    name = StringField()
    size = IntField(min_value=1)
    dtype = StringField(default='float32')
    
    metadata = DictField(default=lambda: {})
    
    def __repr__(self):
        return "<'%s' name='%s', ready=%s>" % (type(self).name, self.name, 'yes' if self.ready else 'no')
    
    
    @property
    def starttime(self):
        return self.block.starttime
    
    @property
    def length(self):
        return self.block.length
    
    
    class Array(object):
        def __init__(self, component, mode):
            import h5py
            self.component = component
            self.mode = mode
            fullpath = self.component.fullpath(create=(mode in ('w', 'a')))
            self.h5file = h5py.File(fullpath, self.mode, driver='stdio')
            if 'data' in self.h5file:
                self.dset = self.h5file['data']
            else:
                self.dset = self.h5file.create_dataset('data',
                    shape=self.component.dataset_shape,
                    dtype=self.component.dtype
                )
        
        def __enter__(self):
            return self.dset
        
        def __exit__(self, type, value, traceback):
            self.close()
        
        def __getitem__(self, *args):
            return self.dset.__getitem__(*args)
        
        def __setitem__(self, *args):
            return self.dset.__setitem__(*args)
        
        def __len__(self):
            return self.dset.__len__()
        
        def len(self):
            return self.dset.len()
        
        def close(self):
            self.h5file.close()
        
        def resize(self, *args):
            return self.dset.resize(*args)
        
        @property
        def shape(self):
            return self.dset.shape
        
        @property
        def dtype(self):
            return self.dset.dtype
        
    
    
    def array(self, mode=None):
        """
        Returns the components content as a wrapper around h5py dataset.
        NB: The optional 'mode' argument is one of the mode required by
            h5py.File(...). Using one of 'w' or 'a' will automatically
            make sure the path to the file is available by creating the
            necessary directories.
        """
        return self.Array(self, mode)
    
    def offspring(self, *Q, **kwargs):
        """
        Returns all child components.
        NB: Q's and keyword arguments can be provided to
            further filter the returned QuerySet object.
        """
        return Component.objects(parent=self, *Q, **kwargs)
    
    
    def grapher(self, params=None):
        if not hasattr(self, '_grapher'):
            self._grapher = self.Grapher(self, params)
        return self._grapher
    
     
    def update(self):
        "Check if processing for child components need to be initiated."
        if self.template:
            for template in self.template.offspring():
                qs = Component.objects(parent=self, template=template)
                if qs.count() == 0:
                    template.create_for_task(self)
    
    def done(self):
        """
        Run basic tasks once a component becomes ready, like initiating
        child components, cached properties and discarding parents content
        if necessary.
        """
        self.ready = True
        self.save()
        
        for key in self.metakeys:
            if key not in self.metadata:
                getattr(self, key)
        
        self.update()
        if self.parent:
            parent = self.parent
            if parent.template and parent.template.discard:
                for template in parent.template.offspring():
                    qs = Component.objects(parent=parent, 
                        template=template, ready=True)
                    if qs.count() == 0:
                        return
                parent.discard()
    
    def read(self):
        "Read content of source file"
        with self.array('w') as array:
            self.block.sourcefile.read_into(self.name, array)
    
    def load(self):
        "Read content and run initiation tasks."
        self.read()
        self.done()
    
    def reload(self):
        "Read content, after it has been discarded."
        self.read()
        self.ready = True
        self.discarded = False
        self.save()
    
    def discard(self, save=True):
        """
        Discard content data.
        NB: Setting the 'save' argument to False will prevent
            the otherwise automatic saving of the DB entry.
        """
        try:
            self.block.dataset.remove(self.path)
        except OSError:
            pass
        
        self.ready = False
        self.discarded = True
        save and self.save()
    
    def delete(self, discard=True):
        """
        Discard content before deleting DB entry.
        NB: Setting 'discard' to False will prevent the
            otherwise automatic discarding of data.
        """
        discard and self.discard(save=False)
        super(Component, self).delete()
    
    
    def criteria_pairs(self):
        from itertools import chain
        for k in chain(self.CriteriaForm.base_fields, 
                ('size', 'length', 'starttime')):
            yield k, getattr(self, k)
    
    
    @property
    def path(self):
        "Relative path of the component's data file"
        return self.block.componentpath("%s.h5" % self.name)
    
    @property
    def available(self):
        return self.ready and self.block.dataset.exists(self.path)
    
    def fullpath(self, create=False):
        """
        Absolute path of the component's data file.
        NB: Setting 'create' to True will make sure the path to
            the file exists, creating the necessary directories.
        """
        return self.block.dataset.path(self.path, create)
    


Component.registry = ObjectList(Component)
