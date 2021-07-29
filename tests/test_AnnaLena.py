import h5py as h5

from prosi3d.sensors.acousticair import Accousticair


acc = Accousticair()
hdf = h5.File('/Users/anna-lenasto/Downloads/4ch_20210428a.h5','r')
acc.get_data(hdf)

#print(acc.xt [:100], acc.yt[:100])

acc.process()

#print(acc.xf [:100], acc.yf [:100])

acc.plot_test()

acc.write()