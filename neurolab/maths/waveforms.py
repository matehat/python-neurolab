from numpy import *
from numpy.random import randn
from scipy.fftpack import fft, ifft

from labo.utils import options
from labo.core.maths.func import *

@options({'limits': (-1., 1.)})
def transition(sampling, length, reverse, opts):
    var = opts['limits']
    X = arange(0., length*sampling)
    amp = var[1] - var[0]
    direction = (-1. if reverse else 1.)
    return (1./(1.+exp(direction*(-10.*X/length + 5.))) - 0.008) * 1.015 * amp + var[0]


@options({
    'states_timeratio': (1., 1.),
    'states_limits': (0, 1.),
    'transition_time': .05,
    'noise_frequency': 300.,
    'noise_variance': 200.,
    'noise_amplitude': 1.,
})
def noise_pulses(sampling, length, frequency, opts):
    transitionT =   opts['transition_time']
    limits =        opts['states_limits']
    states_ratio =  opts['states_timeratio']
    noise = (
        opts['noise_amplitude'],
        opts['noise_frequency'], 
        opts['noise_variance']
    )
    
    N = length * sampling
    cycleN = int(sampling/frequency)
    transitionN = transitionT * sampling
    statesN = [(cycleN - 2*transitionN)*r/sum(states_ratio) 
        for r in states_ratio]
    restN = int(length*frequency % 1) * cycleN
    
    transitionY = [transition(sampling, transitionT, rev, 
        limits=(limits[0], limits[1])) for rev in (False,True)]
    noiseY = (wgn(noise[1], noise[2], sampling, 1/frequency) * 
        noise[0] - (limits[1]-limits[0])/2)
    
    cycleY = concatenate((
        transitionY[0], ones(statesN[0])*limits[1],
        transitionY[1], ones(statesN[1])*limits[0],
    ))
    _N = cycleY.size-statesN[1]
    cycleY[:_N] += cycleY[:_N] * noiseY[:_N]
    
    return concatenate(
        [cycleY for i in range(int(length*frequency))] + 
        [limits[0]*ones(restN)]
    )

@options({
    'states_timeratio': (1., 1.),
    'states_limits': (0, 1.),
    'transition_time': 0.,
    'noise_frequency': 30.,
    'noise_variance': 50.,
    'noise_amplitude': 1.,
})
def mainen_pulses(sampling, length, frequency, opts):
    return noise_pulses(sampling, length, frequency, **opts)


@options({'paddings': (0., 0.)})
def sinusoidal(sampling, length, frequency, opts):
    tlength = length
    N = length * sampling
    cycleN = int(sampling/frequency)
    cyclicN = int(length*frequency // 1) * cycleN
    restN = int(length*frequency % 1) * cycleN
    
    paddingsY = [-1*ones(n*sampling) for n in paddings]
    totalN = cyclicN + paddingsY[0].size + paddingsY[1].size + restN
    
    return array([arange(0., totalN), concatenate([
        paddingsY[0],
        -1*cos(2*pi*frequency * arange(0, cyclicN) * length/cyclicN),
        -1*ones(restN),
        paddingsY[1],
    ])]).transpose()

