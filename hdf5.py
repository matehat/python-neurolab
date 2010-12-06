def to_hdf5(tank, dest=None, blocks=None, groups=None, channels=None):
    from h5py import File as H5File
    import os.path
    
    if not isinstance(tank, Tank):
        tank = Tank(tank)
    if dest is None:
        dest = path
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


if __name__ == '__main__':    
    import argparse
    
    parser = argparse.ArgumentParser(prog='python access.py', usage='%(prog)s path [options]')
    parser.add_argument('path', help="Path to the TDT Tank", nargs="+")
    parser.add_argument('--dest', nargs='*', help="Path to the destination file")
    parser.add_argument('-b', '--block', nargs='*',
        help="Name of the block from which to extract data"
             " (use --describe to see a list of them).")
    parser.add_argument('-c', '--channels', nargs="*",
        help="Name of the channels to include in the extraction. "
             "(use --describe to see a list of them)")
    parser.add_argument('-g', '--groups', nargs="*",
        help="Name of the channel groups to include in the extraction. "
             "(use --describe to see a list of them)")
    
    options = parser.parse_args(sys.argv[1:])
    if options.block is not None:
        for i in range(len(options.block)):
            options.block[i] = options.block[i].replace('_', '-')
    
    if options.dest is not None:
        options.dest = " ".join(options.dest)
    
    to_hdf5(" ".join(options.path), options.dest, options.block, options.groups, options.channels)
