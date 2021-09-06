from prosi3d.sensors.acousticair import Accousticair
from prosi3d.sensors.acousticplatform import Accousticplatform
from prosi3d.sensors.recoater import Recoater

hdf_name = '/Users/anna-lenasto/Documents/Arbeit/Schicht 00581/ch4raw_00581.h5'

acc = Accousticair()
acc.get_data(hdf_name)
acc.process()
#acc.plot_test()
print("Zuordnung")
acc.assignment_position_measurements(hdf_name)
acc.write()


# acc_p = Accousticplatform()
# acc_p.get_data(hdf_name)
# acc_p.process()
# acc_p.plot_test()
# acc_p.write()

# acc_r = Recoater()
# acc_r.get_data(hdf_name)
# acc_r.process()
# acc_r.plot_test()
# acc_r.write()