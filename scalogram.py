from numpy import *
from scipy import *

def hdf5_scalogram(hdf5, fstart, fstop, tw=20., f0=2.5, 
        fdelta=0.25, sampling=1e3, weighting=0.,
        groups=('TUN_',), chunksize=10):
    
    from numpy import arange
    from h5py import File
    
    yn = arange(fstart, fstop, fdelta).size
    if isinstance(groups, basestring):
        groups = (groups,)
    
    if isinstance(hdf5, basestring):
        hdf5 = File(hdf5, 'rw')
    for blockname in hdf5:
        h5_block = hdf5[blockname]
        for groupcode in groups:
            if groupcode in h5_block:
                h5_group = h5_block[groupcode]
                src_sampling = h5_group.attrs['sampling_rate']
                chunkshape = (arange(0, chunksize*sampling/src_sampling).size, yn)
                def chunkindex(j):
                    return (slice(chunkshape[0]*j, chunkshape[0]*(j+1)), slice())
                
                N = chunksize*src_sampling
                scalo = None
                for channel in h5_group:
                    h5_channel = h5_group[channel]
                    original = h5_channel['original']
                    scalo = h5_channel.create_dataset('scalogram', 
                        (h5_channel.size*sampling/src_sampling, yn),
                        dtype=original.dtype)
                    
                    i = 0
                    while i < len(original):
                        chunk = original[i:i+N]
                        scalo[chunkindex(i)] = scalogram(chunk, src_sampling, 
                            fstart, fstop, fdelta, sampling, weighting)
                        i += N
    hdf5.close()            

def scalogram(signal, src_sampling, fstart, fstop, f0=2.5, fdelta=0.25, sampling=1e3, weighting=0.):
    from scipy.fftpack import fft, ifft, fftshift
    from scipy.signal import resample
    from numpy import complex, exp, abs, arange, newaxis
    import numexpr as ne
    
    scales = (f0 / arange(fstart, fstop, fdelta) * sampling)[newaxis, :]
    wlen = signal.size*sampling/src_sampling
    xsd = (arange(-wlen/2., wlen/2.))[:, newaxis] / scales[0, :]
    expn = -1. - weighting
    expn_factor = complex(1j)*2.*pi*f0
    coefs = ne.evaluate('exp(expn_factor*xsd) * exp(-(xsd**2)/2.) * (scales**expn)')
    del xsd, scales
    
    wf = fft(coefs, axis=0).conj()
    del coefs
    sigf = fft(resample(signal, wf.shape[0]))
    wt = abs(fftshift(ifft(sigf[:, newaxis] * wf, axis=0), axes=[0]))
    del wf, sigf
    
    return wt
