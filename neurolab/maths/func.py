from numpy import *
from numpy.random import randn
from scipy.fftpack import fft, ifft

def gauss(mean, dev, x):
    return exp(-((x-mean)/dev)**2. / 2.)

def nextpow2(num):
    return ceil(log(num)/log(2.))

def wgn(frequency, variance, sampling, length):
    """
    A function that returns a white noise numpy array, 
    having a gaussian frequency window centered about
    'frequency', with a variance of 'variance'.
    
    length: length of the noise signal, in seconds
    sampling: sampling of the signal, in hertz
    """
    alength = length*sampling
    y = randn(alength)
    y = fft(y, sampling)
    y = y * gauss(frequency, variance, (arange(0., alength)/length)[:y.size])
    y = real(ifft(y, alength))
    return y/max(y)


__all__ = ['gauss', 'nextpow2', 'wgn']