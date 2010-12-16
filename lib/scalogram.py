from numpy import *
from scipy import *
import time

def nextpow(num, pow):
    return pow**ceil((log(num)/log(pow)))


def hdf5_scalogram(hdf5, fstart, fstop, f0=2.5, 
        fdelta=0.25, sampling=1e3, weighting=0.,
        groups=('TUN_',), chunksize=120.):
    
    from numpy import arange
    from h5py import File
    
    yn = arange(fstart, fstop, fdelta).size
    if isinstance(groups, basestring):
        groups = (groups,)
    
    if isinstance(hdf5, basestring):
        hdf5 = File(hdf5)
    for blockname in hdf5:
        h5_block = hdf5[blockname]
        for groupcode in groups:
            if groupcode in h5_block:
                h5_group = h5_block[groupcode]
                src_sampling = h5_group.attrs['sampling_rate']
                chunkN = nextpow(chunksize*sampling, 2)
                N = chunkN*src_sampling/sampling
                
                def assign(ds, indx, sub):
                    li = indx*chunkN
                    ui = min([(indx+1)*chunkN, ds.shape[0]])
                    ds[li:ui, :] = sub
                
                scalo = None
                for channel in h5_group:
                    h5_channel = h5_group[channel]
                    original = h5_channel['original']
                    if 'scalogram' in h5_channel:
                        del h5_channel['scalogram']
                    scalo = h5_channel.create_dataset('scalogram', 
                        (original.shape[0]*sampling/src_sampling, yn),
                        dtype=original.dtype)
                    
                    i, k = 0, 0
                    while k*N < len(original):
                        chunk = original[k*N:min([(k+1)*N, original.shape[0]])]
                        print "Calculating {}, {chunk.shape}".format(k, chunk=chunk)
                        t = time.time()
                        sg = scalogram(chunk, src_sampling, 
                            fstart, fstop, f0, fdelta, sampling, weighting)
                        print "Finished. {} secs".format(time.time()-t)
                        print "Writing {}".format(k)
                        assign(scalo, k, sg)
                        k += 1
    hdf5.close()            

def scalogram(signal, src_sampling, fstart, fstop, f0=2.5, fdelta=0.25, sampling=1e3, weighting=0.):
    from scipy.fftpack import fft, ifft, fftshift
    from scipy.signal import resample
    from numpy import complex, exp, abs, arange, newaxis, concatenate, zeros
    import numexpr as ne
    
    vlen = signal.size*sampling/src_sampling
    wlen = nextpow(vlen, 2)
    wlens = arange(-wlen/2., wlen/2.)
    sig = concatenate((resample(signal, vlen), zeros(wlen-vlen)))
    
    scales = (f0 / arange(fstart, fstop, fdelta) * sampling)[newaxis, :]
    xsd = wlens[:, newaxis] / scales[0, :]
    expn = -1. - weighting
    expn_factor = complex(1j)*2.*pi*f0
    coefs = ne.evaluate('exp(expn_factor*xsd) * exp(-(xsd**2)/2.) * (scales**expn)')
    del xsd, scales
    
    wf = fft(coefs, axis=0).conj()
    del coefs
    sigf = fft(sig)
    print sigf[:, newaxis].shape, wf[:wlen].shape
    wt = abs(fftshift(ifft(sigf[:, newaxis] * wf[:sigf.size], axis=0), axes=[0]))
    del wf, sigf
    return wt[:vlen]
