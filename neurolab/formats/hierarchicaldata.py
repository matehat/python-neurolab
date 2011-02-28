from neurolab.formats.base import BaseFormat
from os.path import join

try:
    import h5py
    hdf5_enabled = True
except ImportError:
    hdf5_enabled = False

if hdf5_enabled:
    class HDF5Format(BaseFormat):
        slug = 'hierarchical-data'
        writable = True
        
        def __init__(self, sourcefile):
            super(HDF5Format, self).__init__(sourcefile)
        
        
        def h5file(self):
            self.sourcefile.mkdirs()
            return h5py.File(self.sourcefile.fullpath)
        
        def recurse(self, group, name=''):
            items = {}
            for k in group.keys():
                if isinstance(group[k], h5py.Group):
                    items.update(self.recurse(group[k], join(name, k)))
                else:
                    dset_key = join(name, k)
                    dset = group[dset_key]
                    items[dset_key] = dict(dset.attrs.items())
        
        def metadata(self):
            meta = {'length': None}
            h5f = self.h5file()
            meta['waves'] = self.recurse(h5f)
            h5f.close()
            return meta
        
        def read_dataset(self, waves, starttime=0, endtime=None):
            h5f = self.h5file()
            dataset = {}
            for channel in waves:
                dataset[channel] = self.h5f[channel][slice(starttime, endtime)]
            h5f.close()
            return dataset
        
        def write_dataset(self, waves):
            h5f = self.h5file()
            for channel in waves:
                bits = channel.split('/')
                grp = h5f
                while len(bits) > 1:
                    if bits[0] in grp:
                        grp = grp[bits[0]]
                    else:
                        grp = grp.create_group(bits[0])
                    del bits[0]
                if bits[0] in grp:
                    del grp[bits[0]]
                grp.create_dataset(bits[0], data=waves[channel])
            h5f.close()
        
    
    def register_formats(formats):
        formats.extend(HDF5Format)
    
