from prosi3d.sensors.acousticair import Accousticair
from prosi3d.sensors.acousticplatform import Accousticplatform
from prosi3d.sensors.recoater import Recoater

hdf_name = 'data/ch4raw_00593.h5'

acc = Accousticair()
acc_p = Accousticplatform()
acc_r = Recoater()

sensors = [acc,acc_p,acc_r]

for sensor in sensors:
    sensor.get_data(hdf_name)
    sensor.process()
    # No plots for CI
    #sensor.plot_test()
    sensor.write()