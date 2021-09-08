import pytest

from prosi3d.sensors.acousticair import Accousticair
from prosi3d.sensors.acousticplatform import Accousticplatform
from prosi3d.sensors.recoater import Recoater

def test_analysis():
    hdf_name = 'data/ch4raw_00593.h5'

    acc = Accousticair()
    acc.get_data(hdf_name)
    acc.process()
    ## No plots for CI
    #acc.plot_test()
    acc.write()

    acc_p = Accousticplatform()
    acc_p.get_data(hdf_name)
    acc_p.process()
    ## No plots for CI
    #acc_p.plot_test()
    acc_p.write()

    acc_r = Recoater()
    acc_r.get_data(hdf_name)
    acc_r.process()
    # No plots for CI
    #acc_r.plot_test()
    acc_r.write()