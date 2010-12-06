import tdt
from scalogram import scalogram
from matplotlib import pyplot as plt

tank = tdt.Tank(r'C:\Users\Laszlo\Desktop\2010_11_28_ElGreco\20101028ElGreco')
tungs = tank['Block-3'].groupsdict['TUN_']
channel = tungs.channels[0]
chunk = channel[0:30]

sg = scalogram(chunk, channel.sampling_rate, fstart=0.1, fstop=200.)
t = tungs.time_vector(slice(0, 30))

ax = plt.subplot(211)
ax.imshow(sg.transpose(), interpolation='nearest', 
    origin='lower', aspect='normal', 
    extent=(0, 30, 0.1, 200.)
)

ax.set_ylim((0, 200))

ax2 = plt.subplot(212)
ax2.plot(t, chunk)
plt.show()

#plt.savefig('test.pdf')
