from tdt import *

def to_hdf5(tank, dest=None, blocks=None, groups=(), channels=()):
    from h5py import File as H5File
    import os.path
    
    if dest is None:
        dest = tank
    if not isinstance(tank, Tank):
        tank = Tank(tank)
    if os.path.isdir(dest):
        dest = os.path.join(dest, 'datasets.h5')
    if blocks is None:
        blocks = tank.blocks.keys()
    
    h5 = H5File(dest, 'w')
    for blockname in blocks:
        block = tank[blockname]
        block.open()
        
        h5_block = h5.create_group(blockname)
        h5_block.attrs['start'] = block.starttime
        h5_block.attrs['end'] = block.endtime
        
        for group in block.groups:
            if not len(groups) or group.code in groups:
                h5_group = h5_block.create_group(group.code)
                h5_group.attrs['sampling_rate'] = group.sampling_rate
                h5_group.create_dataset('t', data=group.time_vector())
                
                for channel in group.channels:
                    if not len(channels) or channel.name in channels:
                        h5_channel = h5_group.create_group(str(channel.channel))
                        h5_channel.create_dataset('original', data=channel[:])
        
        block.close()
    h5.close()
