import struct, sys, time, os
from datetime import datetime
from collections import namedtuple

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

# Requires Python 2.6

import numpy
from numpy.core.records import fromfile, fromarrays

tsq_dtype = [
    ('size', 'i4'),
    ('type', 'i4'),
    ('code', 'a4'),
    ('channel', 'u2'),
    ('shortcode', 'u2'),
    ('t_start', 'f8'),
    ('eventoffset', 'i8'),
    ('dataformat', 'i4'),
    ('sampling_rate', 'f4'),
]

Types = {
    0x0 : 'EVTYPE_UNKNOWN',
    0x101:'EVTYPE_STRON',
    0x102:'EVTYPE_STROFF',
    0x201:'EVTYPE_SCALER',
    0x8101:'EVTYPE_STREAM',
    0x8201:'EVTYPE_SNIP',
    0x8801: 'EVTYPE_MARK',
}
DataFormats = {
    0 : numpy.dtype('float32'),
    1 : numpy.dtype('int32'),
    2 : numpy.dtype('int16'),
    3 : numpy.dtype('int8'),
    4 : numpy.dtype('float64'),
}

class Tank(object):
    def __init__(self, dirname, nocache=True):
        self.dirname = dirname
        if self.dirname.endswith('/'):
            self.dirname = self.dirname[:-1]
        
        self.name = os.path.basename(self.dirname)
        self.cache = not nocache
    
    def __getitem__(self, blockname):
        return self.blocks[blockname]
    
    
    @property
    def blocks(self):
        if not hasattr(self, '_blocks'):
            self._blocks = OrderedDict()
            for blockname in os.listdir(self.dirname):
                blk = Block(blockname, self)
                if not blk.is_block:
                    continue
            
                self._blocks[blockname] = blk
        return self._blocks
    
    def _block_path(self, block, ext=None):
        if ext is None:
            return os.path.join(self.dirname, block)
        else:
            return os.path.join(self._block_path(block), "%s_%s.%s" % (self.name, block, ext))
    

class Block(object):
    def __init__(self, name, tank):
        self.name = name
        self._signals = OrderedDict()
        self.tank = tank
    
    
    @property
    def groups(self):
        if not hasattr(self, '_groups'):
            self._groups = [Group(self, code) for code in numpy.unique(self.header['code'])]
        return self._groups
    
    @property
    def groupsdict(self):
        if not hasattr(self, '_groupsdict'):
            self._groupsdict = dict([(g.code, g) for g in self.groups])
        return self._groupsdict
    
    @property
    def channels(self):
        if not hasattr(self, '_channels'):
            self._channels = []
            for gr in self.groups:
                self._channels.extend(gr.channels)
        return self._channels
    
    @property
    def channelsdict(self):
        if not hasattr(self, '_channelsdict'):
            self._channelsdict = dict([(ch.name, ch) for ch in self.channels])
        return self._channelsdict
    
    
    @property
    def is_block(self):
        return os.path.exists(self.tsq) and os.path.exists(self.tev)
    
    @property
    def header(self):
        from cPickle import load, dump
        if not hasattr(self, '_header'):
            h = fromfile(self.tsq, tsq_dtype)
            self._header = h[h['type'] == 0x8101] # keep EVTYPE_STREAM only
        return self._header
    
    @property
    def starttime(self):
        if len(self.channels):
            return self.channels[0].starttime
        else:
            return 0
    
    @property
    def endtime(self):
        if len(self.channels):
            return self.channels[0].endtime
        else:
            return 0
    
    @property
    def length(self):
        return self.endtime - self.starttime
    
    @property
    def tev(self):
        return self.tank._block_path(self.name, 'tev')
    
    @property
    def tsq(self):
        return self.tank._block_path(self.name, 'tsq')
    
    
    def open(self):
        if not hasattr(self, 'fid'):
            self.fid = open(self.tev, 'rb')
        return self.fid
    
    def close(self):
        self.fid.close()
        del self.fid
    
    
    def keys(self):
        for channel in self.channels:
            yield channel.name
    
    def iteritems(self):
        for channel in self.channels:
            yield channel.name, channel
    

class Group(object):
    def __init__(self, block, code):
        self.block = block
        self.code = code
    
    
    def time_vector(self, index=None):
        t = numpy.arange(self.totalsize) / self.sampling_rate
        if index is not None:
            index = slice(
                (index.start or 0) * self.sampling_rate,
                (index.stop or 0) * self.sampling_rate
            )
            return t[index]
        else:
            return t
    
    
    @property
    def header(self):
        return self.block.header[self.block.header['code'] == self.code]
    
    @property
    def channels(self):
        if not hasattr(self, '_channels'):
            self._channels = [Channel(self, ch, self.block)
                for ch in self._channel_indices()]
        return self._channels
    
    @property
    def totalsize(self):
        return self.channels[0].totalsize
    
    @property
    def sampling_rate(self):
        return self.channels[0].sampling_rate
    
    @property
    def dtype(self):
        return self.channels[0].dtype
    
    
    def _channel_indices(self):
        return numpy.unique(self.header['channel'])
    

class Channel(object):
    def __init__(self, group, channel, block):
        self.group = group
        self.channel = channel
        self.block = block
    
    def __getitem__(self, index):
        return self.extract(self.block.open(), index)
    
    
    def extract(self, fid, selector):
        bounds = (
            (selector.start or 0) * self.sampling_rate, 
            (selector.stop or self.endtime) * self.sampling_rate
        )
        conditions = (
            (self.bounds['start'] < bounds[0]),
            (self.bounds['start'] < bounds[1]),
            (self.bounds['end'] < bounds[0]),
            (self.bounds['end'] < bounds[1])
        )
        
        return numpy.concatenate(
            # The sector that is split by the first bound
            self.readsectors(fid, conditions[0] & ~conditions[2] & conditions[3], bounds) +
            # All the sectors that fall completely within the bounds
            self.readsectors(fid, ~conditions[0] & conditions[3]) +
            # The sector that is split by the second bound
            self.readsectors(fid, ~conditions[0] & conditions[1] & ~conditions[3], bounds) +
            # The sector that contains the bounds 
            self.readsectors(fid, conditions[0] & ~conditions[3], bounds)
        )
    
    def readsectors(self, fid, conditions, bounds=None):
        def _read(sector):
            fid.seek(sector['eventoffset'])
            return numpy.fromstring(fid.read(sector['size']*4-40), self.dtype)
        
        if bounds is None:
            return [_read(sector) for sector in self.header[conditions]]
        else:
            sector = self.header[conditions]
            if len(sector) == 0:
                return []
            sector = sector[0]
            sectorbounds = self.bounds[conditions][0]
            _bounds = [
                int(bounds[0] - sectorbounds['start']),
                int(bounds[1] - sectorbounds['start'])
            ]
            if _bounds[0] < 0:
                _bounds[0] = 0
            if _bounds[1] > sectorbounds['end']:
                _bounds[1] = None
            return [_read(sector)[slice(*_bounds)]]
    
    def test(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            return key[0] == self.code and key[1] == self.channel
        elif isinstance(key, basestring):
            return key == '%s%s' % (self.code, self.channel) 
    
    
    @property
    def sectorsizes(self):
        return (self.header['size']*4 - 40)/self.itemsize
    
    @property
    def bounds(self):
        if not hasattr(self, '_bounds'):
            start = (self.header['t_start'] - self.starttime) * self.sampling_rate
            self._bounds = fromarrays([start, start + self.sectorsizes - 1], names='start,end')
        return self._bounds
    
    @property
    def code(self):
        return self.group.code
    
    @property
    def header(self):
        if not hasattr(self, '_header'):
            self._header = self.block.header[self.filter]
        return self._header
    
    @property
    def filter(self):
        return (self.block.header['code'] == self.code) & (self.block.header['channel'] == self.channel)
    
    @property
    def name(self):
        return "%s%s" % (self.code, self.channel)
    
    @property
    def itemsize(self):
        return self.dtype.itemsize
    
    @property
    def dtype(self):
        return DataFormats[self.header[0]['dataformat']]
    
    @property
    def totalsize(self):
        return numpy.sum(self.sectorsizes)
    
    @property
    def sampling_rate(self):
        return self.header[0]['sampling_rate']
    
    @property
    def starttime(self):
        return numpy.min(self.header['t_start'])
    
    @property
    def endtime(self):
        return self.starttime + (self.totalsize / self.sampling_rate)
    

