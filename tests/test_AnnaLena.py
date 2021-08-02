import h5py as h5

from prosi3d.sensors.acousticair import Accousticair
from prosi3d.sensors.acousticplatform import Accousticplatform
from prosi3d.sensors.recoater import Recoater

hdf = h5.File('/Users/anna-lenasto/Downloads/4ch_20210428a.h5','r')

acc = Accousticair()
acc.get_data(hdf)
acc.process()
acc.plot_test()
acc.write()

acc_p = Accousticplatform()
acc_p.get_data(hdf)
acc_p.process()
acc_p.plot_test()
acc_p.write()

acc_r = Recoater()
acc_r.get_data(hdf)
acc_r.process()
acc_r.plot_test()
acc_r.write()